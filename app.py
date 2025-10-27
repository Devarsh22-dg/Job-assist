import subprocess, sys

# Ensure spaCy and model are available at runtime
try:
    import spacy
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "spacy==3.7.2"], check=True)
    import spacy

try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_lg"], check=True)
    nlp = spacy.load("en_core_web_lg")

import streamlit as st
from collections import Counter
from datetime import date
from io import StringIO
import re
import spacy
from PyPDF2 import PdfReader
import docx


# -----------------------------
# Domain-Aware + Semantic Keyword Extraction
# -----------------------------

STOPWORDS = set(spacy.lang.en.stop_words.STOP_WORDS)

def extract_ai_keywords(text, max_count=40):
    """Extract technical and domain keywords using NLP."""
    if not text:
        return []

    doc = nlp(text)
    keywords = []

    # Extract named entities (e.g., frameworks, products, organizations)
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "SKILL", "WORK_OF_ART"]:
            if ent.text.lower() not in STOPWORDS and len(ent.text) > 2:
                keywords.append(ent.text.strip())

    # Extract noun chunks (like 'data engineering', 'cloud infrastructure')
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower().strip()
        if (
            all(w not in STOPWORDS for w in chunk_text.split())
            and len(chunk_text.split()) <= 4
        ):
            keywords.append(chunk_text)

    # Clean up and rank by frequency and length
    freq = Counter(keywords)
    ranked = sorted(freq.items(), key=lambda x: (len(x[0].split()), x[1]), reverse=True)
    keywords = [term for term, _ in ranked[:max_count]]

    # Deduplicate, preserve order
    return list(dict.fromkeys(keywords))

# -----------------------------
# Resume Tailoring
# -----------------------------

def tailor_resume(resume_text, job_text):
    keywords = extract_ai_keywords(job_text)
    lines = [l.strip() for l in resume_text.split("\n") if l.strip()]
    tailored_lines = []
    lower_resume = " ".join(lines).lower()

    # Detect missing / related keywords
    missing = [k for k in keywords if k not in lower_resume]

    for line in lines:
        matched = [k for k in keywords if k in line.lower()]
        if matched:
            tailored_lines.append(f"- {line}  (keywords: {', '.join(matched)})")
        else:
            tailored_lines.append(f"- {line}")

    suggestions = [
        f"- Suggested: Mention your experience with '{kw}' or similar skills."
        for kw in missing[:10]
    ]
    return "\n".join(tailored_lines + ["", "--- Suggested Additions ---", *suggestions])

def generate_cover_letter(name, company, position, job_text, summary):
    keywords = extract_ai_keywords(job_text, 10)
    top_keywords = ", ".join(keywords[:6])
    today = date.today().strftime("%B %d, %Y")
    return (
        f"{today}\n\n"
        f"Dear Hiring Team at {company},\n\n"
        f"I am excited to apply for the {position} role. My background aligns strongly with the position, "
        f"particularly in {top_keywords}. {summary}\n\n"
        f"I would welcome the opportunity to contribute to {company}'s growth and innovation.\n\n"
        f"Sincerely,\n{name}"
    )

# -----------------------------
# File Reading
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
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="AI Job Application Agent", layout="wide")

st.title("🤖 AI Job Application Agent (Semantic Keyword Version)")
st.write("This version uses spaCy NLP to detect domain-specific terms, synonyms, and professional jargons from job descriptions.")

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
        keywords = extract_ai_keywords(job_desc, 40)
        tailored_resume = tailor_resume(resume_text, job_desc)
        cover_letter = generate_cover_letter(name, company, position, job_desc, summary)

        st.subheader("🧠 Extracted Domain Keywords (AI-Assisted)")
        st.write(", ".join(keywords))

        st.subheader("📝 Tailored Resume Draft")
        st.text_area("Tailored Resume", tailored_resume, height=300)

        st.subheader("💌 Cover Letter")
        st.text_area("Generated Cover Letter", cover_letter, height=250)

        st.download_button("⬇️ Download Tailored Resume", tailored_resume, file_name="tailored_resume.txt")
        st.download_button("⬇️ Download Cover Letter", cover_letter, file_name="cover_letter.txt")

st.caption("All processing runs locally using spaCy's NLP model. No data is sent externally.")
