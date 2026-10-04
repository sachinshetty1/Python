# Fieldnote Research Desk

A local research workspace for finding sources, extracting readable page text, importing notes, comparing evidence, and drafting cited Markdown reports.

## Run locally

Requires Node.js 20+ and Python 3.10+.

1. Install frontend dependencies: `npm install`
2. Install API dependencies in your chosen Python environment: `pip install -r requirements.txt`
3. Start the API: `uvicorn api.main:app --reload --port 8000`
4. In another terminal, start the UI: `npm run dev`
5. Open the Vite URL shown in the terminal (normally `http://localhost:5173`).

The sample investigation is available immediately. Live web search uses DuckDuckGo through the API and does not require a search API key. Search and page extraction require an internet connection. The app intentionally uses a transparent extractive synthesis rather than claiming to have an LLM; check every finding against its linked source before publication.

## Features

- Search the web for a research question and keep returned sources in a session workspace.
- Import `.txt`, `.md`, `.csv`, and `.json` documents (up to 1 MB each); imported content stays in the browser session.
- Extract readable text from selected public HTML pages (up to 2 MB each).
- Select and compare source excerpts, then generate an editable Markdown report with numbered citations and references.
- Export the report as a `.md` file.

The extraction endpoint only accepts public HTTP/HTTPS hosts, follows a limited number of redirects, and rejects private or local network addresses.
