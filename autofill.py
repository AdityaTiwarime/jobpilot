"""Opens the application form, fills your details, and waits for YOU to review and submit."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

import main
import tracker

FIELDS = {
    "greenhouse": {
        "first_name": ["#first_name", "input[name='first_name']"],
        "last_name": ["#last_name", "input[name='last_name']"],
        "email": ["#email", "input[name='email']"],
        "phone": ["#phone", "input[name='phone']"],
        "linkedin": ["input[aria-label*='LinkedIn' i]", "input[name*='linkedin' i]"],
        "resume": ["input#resume", "input[type='file']"],
    },
    "lever": {
        "full_name": ["input[name='name']"],
        "email": ["input[name='email']"],
        "phone": ["input[name='phone']"],
        "linkedin": ["input[name='urls[LinkedIn]']"],
        "github": ["input[name='urls[GitHub]']"],
        "resume": ["input[name='resume']", "input[type='file']"],
    },
}


def fill_first(page, selectors, value, upload=False):
    for sel in selectors:
        box = page.locator(sel).first
        if box.count():
            box.set_input_files(value) if upload else box.fill(value)
            return True
    return False


def run(job_id):
    cfg = main.load_config()
    me = cfg["profile"]
    job = tracker.get(job_id)
    if not job:
        sys.exit(f"No job with id {job_id}")

    values = {**me, "full_name": f"{me['first_name']} {me['last_name']}",
              "resume": str(Path(me["resume_pdf"]).resolve())}
    fields = FIELDS.get(job["ats"], {})

    with sync_playwright() as p:
        page = p.chromium.launch(headless=False).new_page()
        page.goto(job["url"], wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        if not fields:
            print("Unknown form type - opened the page, fill it manually.")
        for name, selectors in fields.items():
            ok = fill_first(page, selectors, values[name], upload=(name == "resume"))
            print(f"  {'filled ' if ok else 'missing'}  {name}")

        print("\nCheck the form, answer the extra questions, then press Submit yourself.")
        answer = input("Did you submit it? (y/n): ").strip().lower()
        if answer == "y":
            tracker.set_status(job_id, "applied")
            print("Marked as applied ✅")


if __name__ == "__main__":
    run(sys.argv[1])
