import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.evaluation.schemas import Link, Page
from app.core.security import canonicalize, UnsafeURL


def extract_html(html: str, url: str, provider: str, limit: int = 60000) -> Page:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    structured = []
    for tag in soup.select('script[type="application/ld+json"]')[:20]:
        try:
            value = json.loads(tag.string or tag.get_text())
            structured.extend([x for x in (value if isinstance(value, list) else [value]) if isinstance(x, dict)])
        except (ValueError, TypeError):
            pass
    published = soup.select_one('meta[property="article:published_time"], meta[name="date"]')
    published_at = published.get("content") if published else None
    links = []
    for tag in soup.select("a[href]")[:300]:
        try:
            links.append(Link(url=canonicalize(urljoin(url, tag["href"])), text=tag.get_text(" ", strip=True)[:200]))
        except UnsafeURL:
            continue
    tables = [[[cell.get_text(" ", strip=True) for cell in row.select("th,td")]
               for row in table.select("tr")[:100]] for table in soup.select("table")[:20]]
    for tag in soup.select("script,style,noscript,iframe,svg,template"):
        tag.decompose()
    lines = [re.sub(r"\s+", " ", line).strip() for line in soup.get_text("\n").splitlines()]
    text = "\n".join(line for line in lines if line)
    # Table rows preserve label/value associations; JSON-LD is original document data, not an LLM summary.
    extras = [" | ".join(row) for table in tables for row in table if row]
    extras += [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in structured]
    return Page(url=url, title=title, content=(text + "\n" + "\n".join(extras))[:limit],
                provider=provider, links=links, tables=tables, structured=structured,
                published_at=published_at)
