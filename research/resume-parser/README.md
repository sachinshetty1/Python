# AI Resume & Job Matcher

A local Streamlit app that compares a resume with a job description using sentence embeddings, detects skill overlaps and gaps, and suggests focused edits.

## Features

- Upload PDF, DOCX, or TXT resumes and paste a job description.
- Compare meaning with `all-MiniLM-L6-v2` embeddings and cosine similarity.
- Identify matched, missing, and additional skills using a transparent built-in vocabulary.
- Generate deterministic suggestions based on the gaps and similarity score.
- No API key required. The model downloads from Hugging Face on first run.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
python -m unittest -v test_matcher
```

## Notes

The score is a comparison signal, not an interview probability or hiring recommendation. Scanned image-only PDFs need OCR. Vocabulary-based skill detection can miss synonyms and context. Review results and keep all resume claims accurate.
