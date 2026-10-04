from __future__ import annotations

import asyncio
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx
from ddgs import DDGS
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Fieldnote Research API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    max_results: int = Field(default=8, ge=1, le=12)


class ExtractRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg", "nav", "footer", "header"}:
            self.ignored += 1
        elif tag in {"p", "h1", "h2", "h3", "li", "blockquote", "br"} and not self.ignored:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg", "nav", "footer", "header"}:
            self.ignored = max(0, self.ignored - 1)

    def handle_data(self, data: str) -> None:
        if not self.ignored:
            text = " ".join(data.split())
            if text:
                self.parts.append(text)


def _public_host(host: str) -> bool:
    if not host or host.lower() == "localhost" or host.endswith(".localhost"):
        return False
    try:
        addresses = {entry[4][0] for entry in socket.getaddrinfo(host, None)}
    except socket.gaierror:
        return False
    return bool(addresses) and all(ipaddress.ip_address(address).is_global for address in addresses)


def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=400, detail="Only public HTTP and HTTPS URLs can be extracted.")
    if not _public_host(parsed.hostname):
        raise HTTPException(status_code=400, detail="Private or local network addresses are not allowed.")


def _search(query: str, max_results: int) -> list[dict[str, str]]:
    rows = DDGS().text(query, max_results=max_results, region="us-en")
    return [
        {
            "title": str(row.get("title") or "Untitled source"),
            "url": str(row.get("href") or ""),
            "snippet": str(row.get("body") or ""),
            "domain": urlparse(str(row.get("href") or "")).netloc,
        }
        for row in rows
        if row.get("href")
    ]


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/search")
async def search(request: SearchRequest) -> dict[str, list[dict[str, str]]]:
    try:
        results = await asyncio.to_thread(_search, request.query, request.max_results)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Web search is temporarily unavailable.") from exc
    return {"results": results}


@app.post("/api/extract")
async def extract(request: ExtractRequest) -> dict[str, str]:
    current_url = request.url
    headers = {"User-Agent": "FieldnoteResearch/0.1 (+local research workspace)"}

    async with httpx.AsyncClient(follow_redirects=False, timeout=12, trust_env=False) as client:
        for _ in range(5):
            _validate_public_url(current_url)
            try:
                response = await client.get(current_url, headers=headers)
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail="The source could not be reached.") from exc

            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    break
                current_url = urljoin(current_url, location)
                continue
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"The source returned HTTP {response.status_code}.")
            if len(response.content) > 2_000_000:
                raise HTTPException(status_code=413, detail="The source is larger than the 2 MB extraction limit.")
            if "text/html" not in response.headers.get("content-type", ""):
                raise HTTPException(status_code=415, detail="This source is not an HTML page.")

            parser = VisibleText()
            parser.feed(response.text)
            content = " ".join(" ".join(parser.parts).split())[:20_000]
            if not content:
                raise HTTPException(status_code=422, detail="No readable page text was found.")
            return {"url": current_url, "content": content}

    raise HTTPException(status_code=400, detail="The source redirected too many times.")
