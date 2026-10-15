import html
import re

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (personal job tracker)"}


def clean(text):
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def get_json(url, **params):
    r = requests.get(url, params=params, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return r.json()


def remotive(keyword):
    data = get_json("https://remotive.com/api/remote-jobs", search=keyword)
    for j in data.get("jobs", []):
        yield {
            "id": f"remotive-{j['id']}",
            "title": j["title"],
            "company": j["company_name"],
            "location": j.get("candidate_required_location") or "Remote",
            "url": j["url"],
            "description": clean(j.get("description")),
            "source": "remotive",
            "ats": None,
        }


def arbeitnow():
    data = get_json("https://www.arbeitnow.com/api/job-board-api")
    for j in data.get("data", []):
        yield {
            "id": f"arbeitnow-{j['slug']}",
            "title": j["title"],
            "company": j["company_name"],
            "location": ("Remote" if j.get("remote") else "") + " " + (j.get("location") or ""),
            "url": j["url"],
            "description": clean(j.get("description")),
            "source": "arbeitnow",
            "ats": None,
        }


def greenhouse(board):
    data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", content="true")
    for j in data.get("jobs", []):
        yield {
            "id": f"gh-{board}-{j['id']}",
            "title": j["title"],
            "company": board,
            "location": (j.get("location") or {}).get("name", ""),
            "url": j["absolute_url"],
            "description": clean(j.get("content")),
            "source": "greenhouse",
            "ats": "greenhouse",
        }


def lever(company):
    data = get_json(f"https://api.lever.co/v0/postings/{company}", mode="json")
    for j in data:
        yield {
            "id": f"lever-{company}-{j['id']}",
            "title": j["text"],
            "company": company,
            "location": (j.get("categories") or {}).get("location", ""),
            "url": j.get("applyUrl") or j["hostedUrl"],
            "description": clean(j.get("descriptionPlain") or j.get("description")),
            "source": "lever",
            "ats": "lever",
        }


def wanted(job, keywords, locations):
    title = job["title"].lower()
    place = job["location"].lower()
    return any(k in title for k in keywords) and (not place.strip() or any(l in place for l in locations))


def collect(cfg):
    src = cfg["sources"]
    keywords = [k.lower() for k in cfg["search"]["keywords"]]
    locations = [l.lower() for l in cfg["search"]["locations"]]

    feeds = []
    if src.get("remotive"):
        feeds += [(f"remotive:{k}", lambda k=k: remotive(k)) for k in keywords[:4]]
    if src.get("arbeitnow"):
        feeds.append(("arbeitnow", arbeitnow))
    feeds += [(f"greenhouse:{b}", lambda b=b: greenhouse(b)) for b in src.get("greenhouse", [])]
    feeds += [(f"lever:{c}", lambda c=c: lever(c)) for c in src.get("lever", [])]

    seen = {}
    for name, feed in feeds:
        try:
            for job in feed():
                if job["id"] not in seen and wanted(job, keywords, locations):
                    seen[job["id"]] = job
        except Exception as e:
            print(f"  skipped {name}: {e}")
    return list(seen.values())
