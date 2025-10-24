import streamlit as st
from collections import Counter
import re

# --- Keyword and resume logic (same as Flask backend) ---

STOPWORDS = set([
    'a','an','the','and','or','of','to','with','for','in','on','by','as','is','are','be','from','that','this','will','can','must'
])

def extract_keywords(text, max_count=30):
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    freq = Counter(filtered)
    return [w for w, _ in freq.most_common(max_count)]

def tailor_resume(resume_text, keywords):
    if not resume_text:
        return ""
    lines = [l.strip() for l in resume_text.split("\n") if l.strip()]
    lower_keywords = [k.lower() for k in keywords]
    results = []
    for line in lines:
        l_lower = line.lower()
        matched = [k for k in lower_keywords if k in l_lower]
        if matched:
            results.append(f"- {line} (matches: {', '.join(matched)})")
        else:
            results.append(f"- {line}")
    present = " ".join(lines).lower()
    missing = [k for k in keywords if k.lower() not in present]
    suggestions = [f"- Suggested: Demonstrated experience with {k} (add details)." for k in missing[:6]]
    return "\n".join(results + ["", "--- Suggested Additions ---", *suggestions])

def generate_cover_letter(name, company, position, keywords, summary):
    top_keywords = ", ".join(keywords[:6])
    return (
        f"Dear Hiring Team at {company},\n\n"
        f"I am excited to apply for the {position} role. "
        f"My experience aligns strongly with this position, particularly in {top_keywords}. "
        f"{summary}\n\n"
        f"I look forward to contributing to {company}'s success.\n\n"
        f"Sincerely,\n{name}"
    )

# --- Streamlit UI ---

st.set_page_config(page_title="AI Job Application Agent", layout="wide")

st.title("🤖 AI Job Application Agent (Streamlit Version)")
st.write("Tailor your resume to a specific job description, extract keywords, and generate a custom cover letter — all within Streamlit!")

with st.sidebar:
    st.header("Settings")
    name = st.text_input("Your Name", "Your Name")
    company = st.text_input("Company", "Company")
    position = st.text_input("Position", "Position")
    summary = st.text_area("Short Resume Summary", "I have X years of experience delivering measurable results.")

resume = st.text_area("Paste your resume text:", height=200)
job_desc = st.text_area("Paste the job description:", height=200)

if st.button("✨ Tailor Resume"):
    keywords = extract_keywords(job_desc, 40)
    tailored_resume = tailor_resume(resume, keywords)
    cover_letter = generate_cover_letter(name, company, position, keywords, summary)

    st.subheader("📋 Extracted Keywords")
    if keywords:
        st.write(", ".join(keywords))
    else:
        st.info("No keywords extracted — please check your job description input.")

    st.subheader("📝 Tailored Resume Draft")
    st.text_area("Tailored Resume", tailored_resume, height=250)

    st.subheader("💌 Cover Letter")
    st.text_area("Generated Cover Letter", cover_letter, height=200)

    st.download_button("⬇️ Download Tailored Resume", tailored_resume, file_name="tailored_resume.txt")
    st.download_button("⬇️ Download Cover Letter", cover_letter, file_name="cover_letter.txt")

else:
    st.info("Fill in your resume and job description, then click **Tailor Resume** to start.")

st.caption("All processing is done locally in your Streamlit session — no data leaves your browser.")

