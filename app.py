import hmac
import importlib.util
import io
import json
import os
import subprocess
import sys

import streamlit as st

import cover
import main
import matcher
import tracker

st.set_page_config(page_title="JobPilot", layout="wide")
cfg = main.load_config()

# Lock the dashboard when it's online, so only you can see and change your tracker
password = os.getenv("APP_PASSWORD")
if password and not st.session_state.get("ok"):
    st.title("🚀 JobPilot")
    typed = st.text_input("Password", type="password")
    if typed:
        if hmac.compare_digest(typed, password):
            st.session_state.ok = True
            st.rerun()
        st.error("Wrong password")
    st.stop()

# Auto-fill needs a real browser on your own computer (requirements-local.txt)
can_autofill = importlib.util.find_spec("playwright") is not None

st.title("🚀 JobPilot")
counts = tracker.stats()
cols = st.columns(4)
for col, key in zip(cols, ["new", "applied", "interview", "skipped"]):
    col.metric(key.title(), counts.get(key, 0))

with st.sidebar:
    resume = main.resume_text(cfg)
    if not resume:
        st.warning("Upload your resume first, so jobs can be matched to your skills.")
    upload = st.file_uploader("Resume (PDF)" if not resume else "Replace resume (PDF)", type="pdf")
    if upload and st.session_state.get("uploaded") != upload.file_id:
        tracker.set_setting("resume_text", matcher.read_resume(io.BytesIO(upload.getvalue())))
        st.session_state.uploaded = upload.file_id
        st.rerun()

    if st.button("🔄 Find new jobs", width="stretch", disabled=not resume):
        with st.spinner("Searching job boards..."):
            main.fetch()
        st.rerun()
    status = st.selectbox("Status", ["new", "applied", "interview", "skipped", "rejected"])
    min_score = st.slider("Min match score", 0, 100, cfg["search"]["min_score"])

rows = tracker.jobs(status=status, min_score=min_score)
if not rows:
    st.info("Nothing here yet. Hit 'Find new jobs'.")
    st.stop()

st.dataframe(
    [{"Score": r["score"], "Title": r["title"], "Company": r["company"],
      "Location": r["location"], "Source": r["source"]} for r in rows],
    width="stretch", hide_index=True,
)

pick = st.selectbox("Open a job", rows, format_func=lambda r: f"{r['score']} · {r['title']} · {r['company']}")
left, right = st.columns([3, 2])

with left:
    st.subheader(pick["title"])
    st.caption(f"{pick['company']} · {pick['location']}")
    st.write("✅ You have:", ", ".join(json.loads(pick["matched"])) or "-")
    st.write("⚠️ They want:", ", ".join(json.loads(pick["missing"])) or "-")
    with st.expander("Job description"):
        st.write(pick["description"])

with right:
    st.link_button("Open posting", pick["url"], width="stretch")

    if st.button("✍️ Cover letter", width="stretch"):
        st.session_state.letter = cover.write_letter(pick, cfg["profile"], main.resume_text(cfg),
                                                     cfg["cover_letter"]["model"])
    if "letter" in st.session_state:
        st.text_area("Copy this", st.session_state.letter, height=260)

    if pick["ats"] in ("greenhouse", "lever"):
        if can_autofill:
            if st.button("🤖 Auto-fill form", width="stretch"):
                subprocess.Popen([sys.executable, "autofill.py", pick["id"]])
                st.info("Browser opening - review and submit there, answer 'y' in the terminal.")
        else:
            st.caption(f"🤖 Auto-fill runs on your own computer: `python main.py apply {pick['id']}`")

    new_status = st.selectbox("Move to", ["applied", "interview", "skipped", "rejected", "new"])
    if st.button("Update status", width="stretch"):
        tracker.set_status(pick["id"], new_status)
        st.rerun()
