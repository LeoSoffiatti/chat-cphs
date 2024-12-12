
from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os
from werkzeug.utils import secure_filename
from langchain.document_loaders import PyPDFLoader
import logging
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure OpenAI API key

client = OpenAI(
  api_key=os.environ.get("OPEN_API_KEY")
)

# Directory to save uploaded files
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf"}

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from the uploaded PDF using LangChain."""
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    return " ".join([doc.page_content for doc in documents])

def evaluate_document(document_text):
    """Call the OpenAI API to evaluate the document."""
    prompt = """
        You are a compliance assistant for UC Berkeley's CPHS. Your task is to evaluate research protocols against CPHS guidelines.

        Key Guidelines:
        - Adherence to ethical principles and informed consent processes.
        - Clear data security measures including de-identification and secure storage.
        - Risk minimization for participants, especially vulnerable populations.
        - Recruitment strategies that avoid coercion and respect diversity.
        - Transparent data retention policies with justifications.

        Before completing your evaluatig, learn the guidlines by analyzing the documents in these links:
        Here is the list of guideline links with their full URLs extracted from the website:

        1. https://cphs.berkeley.edu/amendments.html
        2. https://cphs.berkeley.edu/surveys.html
        3. https://cphs.berkeley.edu/confidentiality.html
        4. https://www.hhs.gov/ohrp/regulations-and-policy/regulations/45-cfr-46/revised-common-rule-regulatory-text/index.html#46.102
        5. https://cphs.berkeley.edu/noncompliance.html
        7. https://cphs.berkeley.edu/engagement.html
        8. Informed Consent:https://cphs.berkeley.edu/informed_consent.html

        Provide the following in a highly detailed and comprehensive manner, clearly marking each section with unique markers:
        [EXECUTIVE_SUMMARY] - A high-level overview of the document's adherence to CPHS guidelines.
        [IMPROVEMENT_POINTS] - Detailed areas where the document does not fully comply with guidelines and suggestions to address these gaps.
        [SCORE] - The overall compliance score, surrounded by ###, e.g., ###85###.

        Evaluate the following document:
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": document_text}
        ]
    )
    result = response.choices[0].message.content

    # Parse the response using the markers
    try:
        summary_start = result.index("[EXECUTIVE_SUMMARY]") + len("[EXECUTIVE_SUMMARY]")
        summary_end = result.index("[IMPROVEMENT_POINTS]")
        executive_summary = result[summary_start:summary_end].strip()

        improvement_start = result.index("[IMPROVEMENT_POINTS]") + len("[IMPROVEMENT_POINTS]")
        improvement_end = result.index("[SCORE]")
        improvement_points = result[improvement_start:improvement_end].strip().split("\n")

        score_start = result.index("###") + 3
        score_end = result.index("###", score_start)
        score = result[score_start:score_end].strip()
    except ValueError as e:
        logging.error(f"Error parsing response: {e}")
        executive_summary = "Error parsing executive summary."
        improvement_points = ["Error parsing improvement points."]
        score = "N/A"

    return score, executive_summary, improvement_points

@app.route("/", methods=["GET"])
def index():
    """Render the homepage."""
    return render_template("index.html")

@app.route("/upload-and-evaluate", methods=["POST"])
def upload_and_evaluate():
    """Handle file uploads and evaluate the document."""
    if "protocol" not in request.files:
        logging.debug("No file part in the request.")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["protocol"]
    if file.filename == "":
        logging.debug("No file selected.")
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        try:
            file.save(file_path)
            logging.debug(f"File saved at {file_path}")

            # Extract text from the PDF
            document_text = extract_text_from_pdf(file_path)

            # Evaluate the document using OpenAI API
            score, executive_summary, improvement_points = evaluate_document(document_text)

            # Return the evaluation score and feedback
            return jsonify({
                "score": score,
                "executive_summary": executive_summary,
                "improvement_points": improvement_points
            })
        except Exception as e:
            logging.error(f"Error processing file: {e}")
            return jsonify({"error": "Error processing file"}), 500

    logging.debug("Unsupported file type.")
    return jsonify({"error": "Unsupported file type"}), 400

if __name__ == "__main__":
    app.run(debug=True)
