# AI Resume & Job Matcher

A local Streamlit app that compares a resume with a job description using sentence embeddings, surfaces detected skill overlaps and gaps, and suggests focused edits.

## Features

- Upload PDF, DOCX, or TXT resumes and paste a job description.
- Compare document meaning with `all-MiniLM-L6-v2` sentence embeddings and cosine similarity.
- Identify matched, missing, and additional skills using a transparent built-in vocabulary.
- Generate deterministic improvement suggestions grounded in the detected gaps and similarity score.
- Process documents locally. The model downloads from Hugging Face on first use; no API key is needed.

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, then upload a resume and paste a job description. The first analysis downloads the embedding model and may take a little longer.

## Run tests

```bash
python -m unittest -v test_matcher
```

The tests cover skill alias detection, matching, gaps, and suggestion generation without downloading the embedding model.

## Notes

- A similarity score is a signal for comparison, not a hiring recommendation or probability of getting an interview.
- Scanned image-only PDFs need OCR before text can be extracted.
- Skill detection is vocabulary-based and can miss synonyms or context. Review the results and keep resume claims accurate.
- The app truncates each document to 50,000 characters for embedding.
