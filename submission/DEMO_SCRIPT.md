# WebScout AI demonstration script

Target length: 2–3 minutes. The owner must record the video and upload the final MP4/MOV; no video is fabricated in this package.

## Before recording

1. Configure one permitted LLM provider in `.env`.
2. Configure TinyFish if the organizer permits it and live search is needed.
3. Start the app with `scripts/start.ps1`.
4. Open `http://127.0.0.1:8000`.

## Recording sequence

1. **Problem, 15 seconds:** Explain that WebScout answers web questions while exposing the exact source passage instead of returning unsupported model prose.
2. **Simple lookup, 35 seconds:** Ask a factual question with a starting URL. Show the answer, citation URL, supporting passage, retrieval provider, model provider, and elapsed time.
3. **Navigation, 30 seconds:** Ask a question whose answer is one link deeper on the same site. Show the execution stages and bounded retrieval trace.
4. **Structured extraction, 25 seconds:** Use a page containing a table or JSON-LD product field. Show that the cited passage preserves the label/value relationship.
5. **Abstention, 25 seconds:** Ask for a fact absent from the source or contradicted by sources. Show the empty answer and warning instead of a guess.
6. **Architecture, 25 seconds:** Briefly show the `analyze → discover → navigate → extract → verify` flow and explain that claims must be literal substrings of cited evidence.
7. **Close, 15 seconds:** Mention bounded budgets, URL/DNS protections, provider fallback, and the project’s documented AMD compatibility limitations.
