# Project conventions

- Keep the research desk usable without external credentials by preserving its sample-data mode.
- Keep search and source extraction behind the FastAPI `/api` routes.
- Treat imported document text as user-provided content and keep it in the browser session unless explicitly requested otherwise.
- Keep source URLs and citation numbering attached to findings and report exports.
