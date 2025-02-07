from flask import Flask, request, jsonify
import spacy

app = Flask(__name__)

# Load NLP model
nlp = spacy.load("en_core_web_sm")


def extract_keywords(text):
    """Extracts important keywords using NLP"""
    doc = nlp(text.lower())
    keywords = {token.lemma_ for token in doc if token.pos_ in [
        "NOUN", "VERB", "ADJ"] and not token.is_stop}
    return keywords


def calculate_ats_score(resume_text, job_description):
    """Calculates ATS score based on keyword matching"""
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_description)

    matched_keywords = resume_keywords.intersection(job_keywords)
    ats_score = (len(matched_keywords) / len(job_keywords)) * \
        100 if job_keywords else 0

    return round(ats_score, 2), matched_keywords


@app.route("/ats_score", methods=["POST"])
def ats_score():
    """API endpoint to calculate ATS score"""
    data = request.get_json()

    resume_text = data.get("resume_text", "")
    job_description = data.get("job_description", "")

    if not resume_text or not job_description:
        return jsonify({"error": "Both resume_text and job_description are required"}), 400

    ats_score, matched_keywords = calculate_ats_score(
        resume_text, job_description)

    return jsonify({"ATS Score": ats_score, "Matched Keywords": list(matched_keywords)})


if __name__ == "__main__":
    app.run(debug=True)
