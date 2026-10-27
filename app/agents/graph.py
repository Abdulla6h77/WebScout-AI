import asyncio
import hashlib
import time
from contextvars import ContextVar

from langgraph.graph import StateGraph, START, END

from app.agents.planner import analyze
from app.agents.state import AgentState
from app.agents.verifier import verify
from app.core.security import canonicalize, in_scope, UnsafeURL
from app.evaluation.schemas import Answer
from app.retrieval.evidence import collect_evidence
from app.retrieval.ranking import rank


class WebScout:
    def __init__(self, settings, executor, search, llm, guard):
        self.settings, self.executor, self.search, self.llm, self.guard = settings, executor, search, llm, guard
        graph = StateGraph(AgentState)
        for name, fn in [("analyze", self.analyze), ("discover", self.discover), ("navigate", self.navigate),
                         ("extract", self.extract), ("verify", self.verify), ("replan", self.replan)]:
            graph.add_node(name, fn)
        graph.add_edge(START, "analyze")
        graph.add_edge("analyze", "discover")
        graph.add_edge("discover", "navigate")
        graph.add_edge("navigate", "extract")
        graph.add_edge("extract", "verify")
        graph.add_conditional_edges("verify", self.route, {"done": END, "replan": "replan"})
        graph.add_edge("replan", "discover")
        self.graph = graph.compile()

    def traced(self, state, stage, **updates):
        return {**updates, "trace": state["trace"] + [{"stage": stage, "elapsed_ms": round((time.perf_counter() - self._start_context()) * 1000, 2)}]}

    @staticmethod
    def _start_context():
        return STARTED.get()

    async def analyze(self, state):
        plan = analyze(state["query"])
        for url, _ in plan["queue"]:
            await self.guard.validate(url)
            if not in_scope(url, plan["domains"]):
                raise UnsafeURL("Starting URL is outside the domain restriction")
        return self.traced(state, "analyze", **plan)

    async def discover(self, state):
        queue = list(state["queue"])
        warnings = list(state["warnings"])
        if not queue and state["visited"] and state["domains"]:
            return self.traced(state, "discover", queue=[], warnings=warnings)
        if not queue:
            try:
                query = state["search_queries"][min(state["attempt"], 2)]
                links = await self.search.discover(query, state["domains"], min(state["attempt"], 10))
                for link in links:
                    try:
                        url = canonicalize(link.url)
                        if in_scope(url, state["domains"]) and url not in state["visited"]:
                            queue.append((url, 0))
                    except UnsafeURL:
                        continue
                if not links:
                    warnings.append("No discovery results; configure TinyFish or supply a starting URL")
            except Exception:
                warnings.append("Search discovery unavailable")
        return self.traced(state, "discover", queue=list(dict.fromkeys(queue)), warnings=warnings)

    async def navigate(self, state):
        visited, pages = list(state["visited"]), list(state["pages"])
        candidates = [(u, d) for u, d in state["queue"] if u not in visited and d <= self.settings.max_hops]
        slots = min(self.settings.concurrency, self.settings.max_pages - len(visited))
        batch = candidates[:slots]
        queue = candidates[slots:]
        visited.extend(u for u, _ in batch)
        results = await asyncio.gather(*(self.executor.retrieve(u, state["query"].question,
            state["query"].browser_required, state["domains"]) for u, _ in batch), return_exceptions=True)
        hashes = {hashlib.sha256(p.content.encode()).hexdigest() for p in pages}
        failures = state["retrieval_failures"]
        for (_, depth), page in zip(batch, results):
            if isinstance(page, BaseException):
                failures += 1
                continue
            digest = hashlib.sha256(page.content.encode()).hexdigest()
            if digest not in hashes:
                pages.append(page)
                hashes.add(digest)
            if depth < self.settings.max_hops:
                for link in page.links:
                    try:
                        url = canonicalize(link.url)
                        if url not in visited and in_scope(url, state["domains"]):
                            queue.append((url, depth + 1))
                    except UnsafeURL:
                        continue
        queue = list(dict.fromkeys(queue))
        if queue:
            scores = rank(state["query"].question, [u for u, _ in queue])
            queue = [queue[i] for i, _ in scores][:100]
        return self.traced(state, "navigate", visited=visited, pages=pages, queue=queue,
                           retrieval_failures=failures)

    async def extract(self, state):
        evidence = collect_evidence(state["query"].question, state["pages"])
        return self.traced(state, "extract", evidence=evidence)

    async def verify(self, state):
        warnings = list(state["warnings"])
        if state["evidence"]:
            draft, provider, model, failures = await self.llm.extract(
                state["query"].question, state["evidence"], state["query"].exact_answer)
            claims, citations, notes = verify(draft, state["evidence"], state["query"].question)
            warnings.extend(failures + notes)
        else:
            from app.evaluation.schemas import Draft
            draft, provider, model, claims, citations = Draft(), None, None, [], []
        return self.traced(state, "verify", draft=draft, model_provider=provider, model=model,
            claims=claims, citations=citations, warnings=list(dict.fromkeys(warnings)))

    def route(self, state):
        if state["claims"] or state["attempt"] + 1 >= self.settings.max_attempts or len(state["visited"]) >= self.settings.max_pages:
            return "done"
        # Missing model configuration cannot be solved by fetching more pages.
        if state["evidence"] and state["model_provider"] is None:
            return "done"
        if state["visited"] and state["domains"] and not state["queue"]:
            return "done"
        return "replan"

    async def replan(self, state):
        return self.traced(state, "replan", attempt=state["attempt"] + 1)

    async def answer(self, query):
        start = time.perf_counter()
        token = STARTED.set(start)
        initial = AgentState(query=query, queue=[], visited=[], pages=[], evidence=[], attempt=0,
            warnings=[], trace=[], retrieval_failures=0, claims=[], citations=[], model_provider=None, model=None)
        latest = initial
        try:
            async with asyncio.timeout(self.settings.time_budget_s):
                async for snapshot in self.graph.astream(initial, stream_mode="values",
                    config={"recursion_limit": 40}):
                    latest = snapshot
            status = "answered" if latest.get("claims") else ("insufficient_evidence" if latest.get("pages") else "retrieval_failed")
        except TimeoutError:
            status = "timeout"
        except UnsafeURL:
            status = "invalid_request"
            latest["warnings"] = ["Invalid, unsafe, or out-of-scope URL"]
        except Exception:
            status = "retrieval_failed"
            latest["warnings"] = ["Workflow failed; no answer returned"]
        finally:
            STARTED.reset(token)
        return Answer(question=query.question, answer="; ".join(latest.get("claims", [])) if status == "answered" else "",
            status=status, citations=latest.get("citations", []) if status == "answered" else [],
            execution_time_ms=round((time.perf_counter() - start) * 1000, 2),
            retrieval_provider=",".join(sorted({p.provider for p in latest.get("pages", [])})) or None,
            model_provider=latest.get("model_provider"), model=latest.get("model"),
            warnings=latest.get("warnings", []), trace=latest.get("trace", []))


STARTED = ContextVar("webscout_started", default=0.0)
