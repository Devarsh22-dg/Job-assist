import streamlit as st
from collections import Counter
import re
from datetime import date
from io import StringIO
from PyPDF2 import PdfReader
import docx

# -----------------------------
# Keyword Extraction & Tailoring
# -----------------------------
STOPWORDS = set([
    'a','an','the','and','or','of','to','with','for','in','on','by','as','is','are','be','from','that','this','will','can','must'
])

def extract_keywords(text, max_count=40):
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    freq = Counter(filtered)
    return [w for w, _ in freq.most_common(max_count)]

def tailor_resume(resume_text, job_text):
    keywords = extract_keywords(job_text)
    lines = [l.strip() for l in resume_text.split("\n") if l.strip()]
    tailored_lines = []
    lower_resume = " ".join(lines).lower()
    missing = [k for k in keywords if k not in lower_resume]

    for line in lines:
        matched = [k for k in keywords if k in line.lower()]
        if matched:
            tailored_lines.append(f"- {line} (keywords: {', '.join(matched)})")
        else:
            tailored_lines.append(f"- {line}")

    suggestions = [
        f"- Suggested: Include experience with '{kw}' if relevant."
        for kw in missing[:10]
    ]
    return "\n".join(tailored_lines + ["", "--- Suggested Additions ---", *suggestions])

def generate_cover_letter(name, company, position, job_text, summary):
    keywords = extract_keywords(job_text, 10)
    top_keywords = ", ".join(keywords[:6])
    today = date.today().strftime("%B %d, %Y")
    return (
        f"{today}\n\n"
        f"Dear Hiring Team at {company},\n\n"
        f"I am excited to apply for the {position} role. "
        f"My background aligns closely with this opportunity, particularly in {top_keywords}. "
        f"{summary}\n\n"
        f"I look forward to contributing to {company}'s success.\n\n"
        f"Sincerely,\n{name}"
    )

# -----------------------------
# Resume File Handling
# -----------------------------
def read_file(uploaded_file):
    """Read uploaded resume text from TXT, DOCX, or PDF."""
    if uploaded_file is None:
        return ""
    file_type = uploaded_file.name.lower()
    if file_type.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    elif file_type.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text
    elif file_type.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        st.warning("Unsupported file type. Please upload a .txt, .docx, or .pdf file.")
        return ""

# -----------------------------
# Streamlit App UI
# -----------------------------
st.set_page_config(page_title="AI Job Application Agent", layout="wide")

st.title("🤖 AI Job Application Agent")
st.write("Upload your resume and paste a job description to generate tailored application materials automatically!")

with st.sidebar:
    st.header("Settings")
    name = st.text_input("Your Name", "Your Name")
    company = st.text_input("Company", "Company")
    position = st.text_input("Position", "Position")
    summary = st.text_area("Short Resume Summary", "I have X years of experience delivering measurable results.")

uploaded_file = st.file_uploader("📤 Upload your resume (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"])
resume_text = read_file(uploaded_file)

if not resume_text:
    st.info("Please upload your resume file above.")
else:
    st.success("Resume uploaded successfully!")

job_desc = st.text_area("📋 Paste Job Description:", height=200)

if st.button("✨ Tailor Resume"):
    if not job_desc.strip():
        st.warning("Please paste a job description first.")
    else:
        keywords = extract_keywords(job_desc, 40)
        tailored_resume = tailor_resume(resume_text, job_desc)
        cover_letter = generate_cover_letter(name, company, position, job_desc, summary)

        st.subheader("🧩 Extracted Keywords")
        st.write(", ".join(keywords))

        st.subheader("📝 Tailored Resume Draft")
        st.text_area("Tailored Resume", tailored_resume, height=300)

        st.subheader("💌 Cover Letter")
        st.text_area("Generated Cover Letter", cover_letter, height=250)

        st.download_button("⬇️ Download Tailored Resume", tailored_resume, file_name="tailored_resume.txt")
        st.download_button("⬇️ Download Cover Letter", cover_letter, file_name="cover_letter.txt")

st.caption("All processing runs locally in your browser. No data is stored or sent externally.")
