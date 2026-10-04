"""Core matching logic for the AI Resume & Job Matcher."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any


SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "SQL": ("sql", "structured query language"),
    "JavaScript": ("javascript", "js"),
    "TypeScript": ("typescript",),
    "Java": ("java",),
    "C++": ("c++", "cpp"),
    "C#": ("c#", "c sharp"),
    ".NET": (".net", "dotnet", "asp.net"),
    "Go": ("golang",),
    "Rust": ("rust",),
    "React": ("react", "react.js", "reactjs"),
    "Node.js": ("node.js", "nodejs", "node js"),
    "HTML/CSS": ("html", "css"),
    "FastAPI": ("fastapi",),
    "Django": ("django",),
    "Flask": ("flask",),
    "REST APIs": ("rest api", "restful api", "rest apis"),
    "GraphQL": ("graphql",),
    "Machine learning": ("machine learning", "ml"),
    "Deep learning": ("deep learning",),
    "Natural language processing": ("natural language processing", "nlp"),
    "Generative AI": ("generative ai", "genai", "gen ai"),
    "Large language models": ("large language model", "llm", "llms"),
    "PyTorch": ("pytorch", "torch"),
    "TensorFlow": ("tensorflow",),
    "Data analysis": ("data analysis", "data analytics", "analytics"),
    "Pandas": ("pandas",),
    "NumPy": ("numpy",),
    "Tableau": ("tableau",),
    "Power BI": ("power bi",),
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure", "microsoft azure"),
    "Google Cloud": ("google cloud", "gcp"),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "CI/CD": ("ci/cd", "continuous integration", "continuous deployment"),
    "Git": ("git", "github", "gitlab"),
    "PostgreSQL": ("postgresql", "postgres"),
    "MongoDB": ("mongodb", "mongo db"),
    "Redis": ("redis",),
    "Agile": ("agile", "scrum",),
    "Project management": ("project management", "project manager"),
    "Communication": ("communication", "written communication", "verbal communication"),
    "Leadership": ("leadership", "team leadership",),
    "Problem solving": ("problem solving", "problem-solving",),
}


def _contains_phrase(text: str, phrase: str) -> bool:
    """Match a phrase without accidentally matching it inside a larger word."""
    pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def extract_skills(text: str, skills: dict[str, Iterable[str]] | None = None) -> set[str]:
    """Return canonical skills whose names or aliases occur in the text."""
    catalog = skills or SKILL_ALIASES
    found = set()
    for skill, aliases in catalog.items():
        if _contains_phrase(text, skill) or any(_contains_phrase(text, alias) for alias in aliases):
            found.add(skill)
    return found


def compare_skills(resume_text: str, job_text: str) -> dict[str, set[str]]:
    """Compare detected resume skills with the requirements in a job description."""
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_text)
    return {
        "resume": resume_skills,
        "job": job_skills,
        "matched": resume_skills & job_skills,
        "missing": job_skills - resume_skills,
        "additional": resume_skills - job_skills,
    }


def build_suggestions(skill_gaps: dict[str, set[str]], similarity: float) -> list[str]:
    """Create specific, truthful next steps from the comparison results."""
    missing = sorted(skill_gaps["missing"])
    suggestions = []

    if missing:
        priority = ", ".join(missing[:5])
        suggestions.append(
            f"If you have hands-on experience with {priority}, add a concise proof point "
            "to your experience or projects section."
        )
    if skill_gaps["matched"]:
        strongest = ", ".join(sorted(skill_gaps["matched"])[:4])
        suggestions.append(
            f"Bring your relevant experience with {strongest} into the top third of your resume."
        )
    if similarity < 0.45:
        suggestions.append(
            "Mirror the role's language where it accurately describes your work, and tailor "
            "your summary to the responsibilities in this posting."
        )
    elif similarity < 0.7:
        suggestions.append(
            "Add measurable outcomes to the most relevant bullets so the connection to this "
            "role is easy to scan."
        )
    else:
        suggestions.append(
            "Strengthen your best-matched examples with scope and measurable outcomes, such "
            "as time saved, revenue, or users supported."
        )
    suggestions.append(
        "Keep every claim accurate; add a project or training entry before listing a skill "
        "you have not used yet."
    )
    return suggestions


def semantic_similarity(
    resume_text: str,
    job_text: str,
    model_name: str,
    model: Any | None = None,
) -> float:
    """Encode both documents and return their cosine similarity as a 0-100 score."""
    from sklearn.metrics.pairwise import cosine_similarity

    if model is None:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(model_name)
    vectors = model.encode([resume_text, job_text], convert_to_numpy=True)
    score = float(cosine_similarity([vectors[0]], [vectors[1]])[0][0])
    return max(0.0, min(1.0, score))
