import json
import os

import requests


def template_letter(job, profile):
    skills = ", ".join(json.loads(job["matched"])[:5]) or "Python and problem solving"
    return (
        f"Dear Hiring Team at {job['company']},\n\n"
        f"I'm applying for the {job['title']} role. I'm a Computer Science graduate who "
        f"builds practical projects with {skills}, and the work described in this posting "
        f"lines up closely with what I enjoy doing.\n\n"
        f"I pick up new tools quickly, I'm comfortable owning a task end to end, and I can "
        f"join immediately. I'd be glad to walk you through my projects on GitHub "
        f"({profile['github']}).\n\n"
        f"Thank you for your time.\n{profile['first_name']} {profile['last_name']}\n"
        f"{' | '.join(x for x in (profile['email'], profile['phone']) if x)}"
    )


def write_letter(job, profile, resume_text, model):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return template_letter(job, profile)

    prompt = (
        "Write a short, honest cover letter (under 200 words) in plain first person. "
        "Only use facts from the resume. No buzzwords.\n\n"
        f"JOB: {job['title']} at {job['company']}\n{job['description'][:3000]}\n\n"
        f"RESUME:\n{resume_text[:4000]}"
    )
    model = os.getenv("GEMINI_MODEL", model)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        r = requests.post(url, params={"key": key}, timeout=60,
                          json={"contents": [{"parts": [{"text": prompt}]}]})
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"AI letter failed ({e}), using template")
        return template_letter(job, profile)
