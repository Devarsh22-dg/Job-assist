import streamlit as st
from collections import Counter
import re
from datetime import date
from io import StringIO
from PyPDF2 import PdfReader
import docx

python -c "from PyPDF2 import PdfReader; print('PyPDF2 is installed')"

# -----------------------------
# Domain-Aware Keyword Extraction
# -----------------------------

# Common English words, connectors, verbs — all ignored
STOPWORDS = set("""
a an the and or but for from in on to with by as at of be been being am is are was were will can must 
should could may might would have has had do does did not your their our my its you they we i this that
these those such other more some many few about it them us her him she he where when how what who which
if then else than because since until while although though before after above below between during per 
each every own same so very into over under around out up down off across near far much also even 
""".split())

def extract_jargon_keywords(text, max_count=40):
    """Extract technical / domain jargons and exclude grammar or filler words."""
    if not text:
        return []
    # Extract multiword technical patterns like "machine learning", "data analysis"
    phrases = re.findall(r'\b[a-zA-Z]{3,}(?:\s+[a-zA-Z]{3,}){0,2}\b', text.lower())
    filtered = [
        p.strip() for p in phrases
        if not all(w in STOPWORDS for w in p.split())
        and len(p.split()) <= 3
        and not p.isdigit()
    ]
    freq = Counter(filtered)
    # Prioritize longer multiword terms (jargons) slightly higher
    ranked = sorted(freq.items(), key=lambda x: (len(x[0].split()), x[1]), reverse=True)
    keywords = [term for term, _ in ranked[:max_count]]
    return list(dict.fromkeys(keywords))  # remove duplicates preserving order

# -----------------------------
# Resume Tailoring Functions
# -----------------------------

def tailor_resume(resume_text, job_text):
    keywords = extract_jargon_keywords(job_text)
    lines = [l.strip() for l in resume_text.split("\n") if l.strip()]
    tailored_lines = []
    lower_resume = " ".join(lines).lower()
    missing = [k for k in keywords if k not in lower_resume]

    for line in lines:
        matched = [k for k in keywords if k in line.lower()]
        if matched:
            tailored_lines.append(f"- {line}  (keywords: {', '.join(matched)})")
        else:
            tailored_lines.append(f"- {line}")

    suggestions = [
        f"- Suggested: Add details or examples demonstrating experience with '{kw}'."
        for kw in missing[:10]
    ]
    return "\n".join(tailored_lines + ["", "--- Suggested Additions ---", *suggestions])

def generate_cover_letter(name, company, position, job_text, summary):
    keywords = extract_jargon_keywords(job_text, 10)
    top_keywords = ", ".join(keywords[:6])
    today = date.today().strftime("%B %d, %Y")
    return (
        f"{today}\n\n"
        f"Dear Hiring Team at {company},\n\n"
        f"I am excited to apply for the {position} role. My background aligns closely with this opportunity, "
        f"especially in areas such as {top_keywords}. {summary}\n\n"
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

st.title("🤖 AI Job Application Agent (Domain-Aware Version)")
st.write("This version intelligently extracts domain-specific keywords and jargons from job descriptions — ignoring grammar words and filler text.")

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
        keywords = extract_jargon_keywords(job_desc, 40)
        tailored_resume = tailor_resume(resume_text, job_desc)
        cover_letter = generate_cover_letter(name, company, position, job_desc, summary)

        st.subheader("🧩 Extracted Domain Keywords")
        st.write(", ".join(keywords))

        st.subheader("📝 Tailored Resume Draft")
        st.text_area("Tailored Resume", tailored_resume, height=300)

        st.subheader("💌 Cover Letter")
        st.text_area("Generated Cover Letter", cover_letter, height=250)

        st.download_button("⬇️ Download Tailored Resume", tailored_resume, file_name="tailored_resume.txt")
        st.download_button("⬇️ Download Cover Letter", cover_letter, file_name="cover_letter.txt")

st.caption("All processing runs locally in your browser. Domain-aware keyword extraction uses text patterns and term frequency — no data leaves your system.")
