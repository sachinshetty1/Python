from __future__ import annotations

from html import escape
from io import BytesIO
from pathlib import Path

import streamlit as st
from docx import Document
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from matcher import build_suggestions, compare_skills, semantic_similarity


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAX_TEXT_LENGTH = 50_000

st.set_page_config(
    page_title="Resume / Role Matcher",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
        --ink: #202926;
        --muted: #69736e;
        --paper: #f4f5f1;
        --white: #ffffff;
        --line: #dfe4de;
        --green: #176b52;
        --green-soft: #e5f1eb;
        --coral: #c45b43;
        --coral-soft: #f8e9e3;
        --gold: #b17b21;
        --gold-soft: #f5eedc;
    }

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    .stApp { background: var(--paper); }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem; }
    h1, h2, h3 { font-family: 'Manrope', sans-serif !important; color: var(--ink); letter-spacing: 0 !important; }
    .eyebrow { font: 500 0.72rem 'DM Mono', monospace; text-transform: uppercase; color: var(--green); letter-spacing: 0.08em; }
    .page-title { font: 800 2.45rem/1.12 'Manrope', sans-serif; margin: 0.45rem 0 0.5rem; }
    .page-subtitle { color: var(--muted); font-size: 1rem; max-width: 690px; margin-bottom: 1.6rem; }
    .section-label { font: 500 0.72rem 'DM Mono', monospace; color: var(--muted); text-transform: uppercase; margin-bottom: 0.55rem; }
    .input-shell { background: var(--white); border: 1px solid var(--line); border-radius: 7px; padding: 1.05rem 1.15rem 0.8rem; min-height: 100%; }
    .input-title { font: 700 1rem 'Manrope', sans-serif; margin-bottom: 0.65rem; }
    .input-note { font-size: 0.83rem; color: var(--muted); }
    .stTextArea textarea { background: #fff; border-color: var(--line); border-radius: 5px; font-size: 0.92rem; }
    [data-testid="stFileUploader"] { background: #fff; border: 1px dashed #b8c8bc; border-radius: 5px; }
    .stButton > button[kind="primary"] { background: var(--green); border: 1px solid var(--green); color: #fff; border-radius: 5px; font-weight: 700; min-height: 2.8rem; }
    .stButton > button[kind="primary"]:hover { background: #10533f; border-color: #10533f; }
    .result-rule { border-top: 1px solid var(--line); margin: 1.8rem 0; }
    .score-panel { background: var(--ink); color: white; padding: 1.4rem 1.5rem; border-radius: 7px; min-height: 175px; }
    .score-label { color: #b9c9c0; text-transform: uppercase; font: 500 0.72rem 'DM Mono', monospace; }
    .score-value { color: #fff; font: 800 3.15rem/1.1 'Manrope', sans-serif; margin: 0.4rem 0 0.2rem; }
    .score-copy { color: #d1dbd5; font-size: 0.88rem; }
    .metric-strip { border: 1px solid var(--line); background: white; border-radius: 7px; padding: 1.05rem 1.2rem; height: 100%; }
    .metric-number { font: 700 1.65rem 'Manrope', sans-serif; }
    .metric-caption { color: var(--muted); font-size: 0.83rem; margin-top: 0.15rem; }
    .skill-heading { font: 700 1.12rem 'Manrope', sans-serif; margin: 0 0 0.3rem; }
    .skill-help { color: var(--muted); font-size: 0.87rem; margin-bottom: 0.85rem; }
    .skill-chip { display: inline-block; font-size: 0.82rem; font-weight: 600; border-radius: 4px; padding: 0.38rem 0.62rem; margin: 0.18rem 0.22rem 0.18rem 0; }
    .chip-match { background: var(--green-soft); color: #15543f; }
    .chip-gap { background: var(--coral-soft); color: #913e2e; }
    .chip-extra { background: #e9ece9; color: #48524c; }
    .suggestion { border-left: 3px solid var(--gold); padding: 0.72rem 0.85rem; background: var(--gold-soft); margin: 0.5rem 0; font-size: 0.9rem; border-radius: 0 4px 4px 0; }
    .privacy-note { color: var(--muted); font-size: 0.78rem; margin-top: 0.4rem; }
    .stProgress > div > div { background-color: var(--green); }
    @media (max-width: 700px) {
        .block-container { padding: 1.4rem 1rem 3rem; }
        .page-title { font-size: 2rem; }
        .score-panel { min-height: auto; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def get_embedding_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def extract_resume_text(uploaded_file) -> str:
    extension = Path(uploaded_file.name).suffix.lower()
    content = uploaded_file.getvalue()
    if extension == ".pdf":
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if extension == ".docx":
        document = Document(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    if extension == ".txt":
        return content.decode("utf-8", errors="replace")
    raise ValueError("Use a PDF, DOCX, or TXT file.")


def render_skill_chips(skills: set[str], class_name: str, empty_label: str) -> None:
    if not skills:
        st.caption(empty_label)
        return
    chips = "".join(
        f'<span class="skill-chip {class_name}">{escape(skill)}</span>'
        for skill in sorted(skills)
    )
    st.markdown(chips, unsafe_allow_html=True)


st.markdown('<div class="eyebrow">Career toolkit / 01</div>', unsafe_allow_html=True)
st.markdown('<div class="page-title">Resume / Role Matcher</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">See how your experience maps to a role. Compare meaning, '
    'surface the skills to address, and leave with practical edits.</div>',
    unsafe_allow_html=True,
)

resume_column, job_column = st.columns(2, gap="large")
with resume_column:
    st.markdown('<div class="input-shell">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">01 / Your experience</div>', unsafe_allow_html=True)
    st.markdown('<div class="input-title">Upload a resume</div>', unsafe_allow_html=True)
    uploaded_resume = st.file_uploader(
        "Resume file",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
        help="PDF, DOCX, or plain text. Text is extracted locally.",
    )
    st.markdown('<div class="input-note">PDF, DOCX, or TXT · up to 10 MB</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
with job_column:
    st.markdown('<div class="input-shell">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">02 / The opportunity</div>', unsafe_allow_html=True)
    st.markdown('<div class="input-title">Paste the job description</div>', unsafe_allow_html=True)
    job_description = st.text_area(
        "Job description",
        key="job_description",
        height=195,
        placeholder="Paste the role summary, responsibilities, and requirements...",
        label_visibility="collapsed",
        max_chars=MAX_TEXT_LENGTH,
    )
    st.markdown('<div class="input-note">Include responsibilities and requirements for a more useful comparison.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

analyze_column, privacy_column = st.columns([1, 2], vertical_alignment="center")
with analyze_column:
    analyze = st.button("Analyze match", type="primary", use_container_width=True)
with privacy_column:
    st.markdown(
        '<div class="privacy-note">Your documents are processed in this app session. '
        'The embedding model runs locally after its first download.</div>',
        unsafe_allow_html=True,
    )

if analyze:
    if uploaded_resume is None:
        st.error("Upload a resume before running the comparison.")
    elif not job_description.strip():
        st.error("Paste a job description before running the comparison.")
    else:
        try:
            resume_text = extract_resume_text(uploaded_resume).strip()
            if not resume_text:
                st.error("No readable text found. Scanned PDFs need OCR before they can be compared.")
            else:
                resume_text = resume_text[:MAX_TEXT_LENGTH]
                job_text = job_description.strip()[:MAX_TEXT_LENGTH]
                with st.spinner("Encoding both documents and comparing their meaning..."):
                    model = get_embedding_model(MODEL_NAME)
                    similarity = semantic_similarity(resume_text, job_text, MODEL_NAME, model=model)
                skills = compare_skills(resume_text, job_text)
                suggestions = build_suggestions(skills, similarity)
                st.session_state["analysis"] = {
                    "similarity": similarity,
                    "skills": skills,
                    "suggestions": suggestions,
                    "resume_name": uploaded_resume.name,
                }
        except Exception as error:
            st.error(f"Could not analyze this file: {error}")

analysis = st.session_state.get("analysis")
if analysis:
    st.markdown('<div class="result-rule"></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Your results</div>', unsafe_allow_html=True)
    st.markdown(f"### Compared with `{analysis['resume_name']}`")
    similarity = analysis["similarity"]
    skills = analysis["skills"]

    score_column, matched_column, gap_column = st.columns([1.15, 1, 1], gap="medium")
    with score_column:
        st.markdown(
            f'<div class="score-panel"><div class="score-label">Semantic similarity</div>'
            f'<div class="score-value">{similarity:.0%}</div>'
            '<div class="score-copy">Meaning-level alignment across both documents</div></div>',
            unsafe_allow_html=True,
        )
        st.progress(similarity, text="Embedding similarity")
    with matched_column:
        st.markdown(
            f'<div class="metric-strip"><div class="metric-number">{len(skills["matched"])}</div>'
            '<div class="metric-caption">Detected skills in common</div></div>',
            unsafe_allow_html=True,
        )
    with gap_column:
        st.markdown(
            f'<div class="metric-strip"><div class="metric-number">{len(skills["missing"])}</div>'
            '<div class="metric-caption">Detected skills not found in resume</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    left_result, right_result = st.columns(2, gap="large")
    with left_result:
        st.markdown('<div class="skill-heading">Skill overlap</div>', unsafe_allow_html=True)
        st.markdown('<div class="skill-help">Skills detected in both documents</div>', unsafe_allow_html=True)
        render_skill_chips(skills["matched"], "chip-match", "No shared skills detected from the built-in skill list.")
        st.markdown('<br><div class="skill-heading">Potential gaps</div>', unsafe_allow_html=True)
        st.markdown('<div class="skill-help">Present in the job description, not detected in your resume</div>', unsafe_allow_html=True)
        render_skill_chips(skills["missing"], "chip-gap", "No listed skill gaps detected.")
        if skills["additional"]:
            st.markdown('<br><div class="skill-heading">Other detected strengths</div>', unsafe_allow_html=True)
            st.markdown('<div class="skill-help">Detected in your resume, not in the job description</div>', unsafe_allow_html=True)
            render_skill_chips(skills["additional"], "chip-extra", "")
    with right_result:
        st.markdown('<div class="skill-heading">Improvement ideas</div>', unsafe_allow_html=True)
        st.markdown('<div class="skill-help">Use only suggestions that accurately reflect your experience</div>', unsafe_allow_html=True)
        for suggestion in analysis["suggestions"]:
            st.markdown(f'<div class="suggestion">{escape(suggestion)}</div>', unsafe_allow_html=True)
        st.caption("Skill detection uses a built-in vocabulary; review the document before making edits.")
