import asyncio
import ipaddress
import re
import socket
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class UnsafeURL(ValueError):
    pass


def canonicalize(url: str) -> str:
    if len(url) > 2048 or re.search(r"[\x00-\x20\\]", url):
        raise UnsafeURL("Invalid URL characters")
    try:
        p = urlsplit(url)
        if p.scheme.lower() not in {"http", "https"} or not p.hostname:
            raise UnsafeURL("Only absolute HTTP(S) URLs are supported")
        if p.username or p.password or p.port not in (None, 80, 443):
            raise UnsafeURL("Credentials and non-web ports are prohibited")
        host = p.hostname.encode("idna").decode().lower().rstrip(".")
        if host in {"localhost", "metadata.google.internal"} or host.endswith((".local", ".internal", ".localhost")):
            raise UnsafeURL("Private hosts are prohibited")
        try:
            if not ipaddress.ip_address(host).is_global:
                raise UnsafeURL("Private and reserved addresses are prohibited")
        except ValueError as exc:
            if isinstance(exc, UnsafeURL):
                raise
        netloc = f"[{host}]" if ":" in host else host
        if p.port and (p.scheme, p.port) not in {("http", 80), ("https", 443)}:
            netloc += f":{p.port}"
        query = urlencode(sorted((k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                                 if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}))
        return urlunsplit((p.scheme.lower(), netloc, p.path or "/", query, ""))
    except (ValueError, UnicodeError) as exc:
        raise UnsafeURL("Invalid or unsafe URL") from exc


def in_scope(url: str, domains: list[str]) -> bool:
    host = urlsplit(url).hostname or ""
    return not domains or any(host == d or host.endswith("." + d) for d in domains)


class URLGuard:
    async def resolve(self, url: str) -> tuple[str, str]:
        url = canonicalize(url)
        p = urlsplit(url)
        try:
            records = await asyncio.get_running_loop().getaddrinfo(
                p.hostname, p.port or (443 if p.scheme == "https" else 80), type=socket.SOCK_STREAM)
        except OSError as exc:
            raise UnsafeURL("Host could not be resolved") from exc
        if not records or any(not ipaddress.ip_address(row[4][0]).is_global for row in records):
            raise UnsafeURL("Host resolves to a private or reserved address")
        return url, records[0][4][0]

    async def validate(self, url: str) -> str:
        url, _ = await self.resolve(url)
        return url


INJECTION = re.compile(
    r"ignore (?:all |any |the |previous )*(?:instructions|prompts)|"
    r"system\s*(?:prompt|message)|developer message|reveal.*(?:secret|key)|"
    r"(?:answer|respond|output) (?:only |with )?['\"]?hacked|"
    r"you are (?:now |an? )|follow these instructions", re.I)


def suspicious(text: str) -> bool:
    return bool(INJECTION.search(text))
