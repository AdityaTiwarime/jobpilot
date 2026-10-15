import os
import sys
from pathlib import Path

import yaml

import matcher
import sources
import tracker


def load_config():
    with open("config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # Private details (phone etc.) can live in env vars / Streamlit secrets instead of the public repo
    for field in cfg["profile"]:
        val = os.getenv(f"PROFILE_{field.upper()}")
        if val:
            cfg["profile"][field] = val
    return cfg


def resume_text(cfg):
    """resume.pdf next to the code if present, else the copy uploaded from the dashboard."""
    path = Path(cfg["profile"]["resume_pdf"])
    if path.exists():
        return matcher.read_resume(path)
    return tracker.get_setting("resume_text", "")


def fetch():
    cfg = load_config()
    keywords = cfg["search"]["keywords"]
    resume = resume_text(cfg)
    if not resume:
        print("No resume found - add resume.pdf or upload it on the dashboard first.")
        return
    my_skills = matcher.find_skills(resume)
    print(f"Your skills: {', '.join(sorted(my_skills))}\nFetching jobs...")

    found = sources.collect(cfg)
    for job in found:
        job["score"], job["matched"], job["missing"] = matcher.score(job, my_skills, keywords)

    added = tracker.save(found)
    print(f"Checked {len(found)} matching jobs, {added} new saved.")


def show():
    cfg = load_config()
    for j in tracker.jobs(status="new", min_score=cfg["search"]["min_score"])[:30]:
        print(f"[{j['score']:>3}] {j['title'][:45]:45} | {j['company'][:18]:18} | {j['id']}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    if cmd == "fetch":
        fetch()
    elif cmd == "list":
        show()
    elif cmd == "apply":
        import autofill
        autofill.run(sys.argv[2])
    else:
        print("Usage: python main.py [fetch | list | apply <job_id>]")
