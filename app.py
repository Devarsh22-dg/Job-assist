from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from collections import Counter

app = Flask(__name__)
CORS(app)

# Common stopwords to ignore in keyword extraction
STOPWORDS = set([
    'a','an','the','and','or','of','to','with','for','in','on','by',
    'as','is','are','be','from','that','this','will','can','must'
])

def extract_keywords(text, max_words=30):
    """Extract top keywords from job description."""
    if not text:
        return []
    words = re.findall(r'[A-Za-z]+', text.lower())
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 2]
    freq = Counter(filtered)
    return [w for w, _ in freq.most_common(max_words)]

def tailor_resume(resume_text, keywords):
    """Mark lines with keyword matches and suggest new bullet points."""
    lines = [l.strip() for l in resume_text.split('\n') if l.strip()]
    results = []
    lower_keywords = [k.lower() for k in keywords]

    for line in lines:
        matched = [k for k in lower_keywords if k in line.lower()]
        if matched:
            results.append(f"- {line}  (matches: {', '.join(matched)})")
        else:
            results.append(f"- {line}")

    present = set(' '.join(lines).lower())
    missing = [k for k in keywords if k.lower() not in present]
    suggestions = [
        f"- Suggested: Demonstrated experience with {k} (describe a specific project or outcome)."
        for k in missing[:6]
    ]

    return '\n'.join(results + ['\n--- Suggested additions ---'] + suggestions)

def generate_cover_letter(name, company, position, keywords, summary):
    """Generate a short personalized cover letter."""
    top_keywords = ', '.join(keywords[:6])
    return f"""Dear Hiring Team at {company},

I am excited to apply for the {position} role. I bring experience that aligns with your needs — particularly in {top_keywords}. {summary}

I look forward to discussing how my background can contribute to {company}'s success.

Sincerely,
{name}
"""

@app.route('/api/tailor', methods=['POST'])
def api_tailor():
    """API endpoint to tailor resume and generate cover letter."""
    data = request.get_json()
    resume = data.get('resume', '')
    jd = data.get('job_desc', '')
    name = data.get('name', 'Your Name')
    company = data.get('company', 'Company')
    position = data.get('position', 'Position')
    summary = data.get('summary', 'I have X years experience delivering measurable results.')

    keywords = extract_keywords(jd, 40)
    tailored = tailor_resume(resume, keywords)
    cover = generate_cover_letter(name, company, position, keywords, summary)

    return jsonify({
        'keywords': keywords,
        'tailored': tailored,
        'cover': cover
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
