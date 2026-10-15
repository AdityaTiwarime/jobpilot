import re
from pathlib import Path

SKILLS = {
    "python", "django", "flask", "fastapi", "sql", "postgresql", "mysql", "mongodb",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "machine learning",
    "nlp", "llm", "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux",
    "react", "javascript", "typescript", "node", "rest", "api", "spark", "airflow",
    "excel", "power bi", "tableau", "selenium", "pytest", "ci/cd", "bash",
    "prometheus", "grafana", "terraform", "redis", "kafka", "html", "css",
}
SENIOR = re.compile(r"\b(senior|sr\.?|lead|principal|staff|manager|director|head)\b", re.I)


def read_resume(path):
    """Takes a file path, or the raw PDF from the dashboard's upload box."""
    from pypdf import PdfReader
    if not isinstance(path, (str, Path)):
        return " ".join(page.extract_text() or "" for page in PdfReader(path).pages)
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        return " ".join(page.extract_text() or "" for page in PdfReader(p).pages)
    return p.read_text(encoding="utf-8")


def find_skills(text):
    t = text.lower()
    return {s for s in SKILLS if re.search(rf"(?<![a-z]){re.escape(s)}(?![a-z])", t)}


def score(job, my_skills, keywords):
    needed = find_skills(job["title"] + " " + job["description"])
    hit = needed & my_skills
    skill_part = len(hit) / len(needed) if needed else 0.5
    title_hit = any(k.lower() in job["title"].lower() for k in keywords)

    total = 70 * skill_part + 30 * title_hit
    if SENIOR.search(job["title"]):
        total -= 25
    return round(max(0, min(100, total))), sorted(hit), sorted(needed - my_skills)
