import os
import json
import shutil
import re
import fitz

from dotenv import load_dotenv
from google import genai

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# -----------------------------
# Load Gemini API Key
# -----------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=API_KEY)

# -----------------------------
# Templates
# -----------------------------
templates = Jinja2Templates(directory="templates")

# -----------------------------
# Folders
# -----------------------------
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# -----------------------------
# Home Page
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "result": None,
            "error": None
        }
    )

# -----------------------------
# Upload Resume
# -----------------------------
@app.post("/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):

    try:

        # Check file selected
        if not file.filename:

            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "result": None,
                    "error": "Please choose a PDF."
                }
            )

        # Check extension
        if not file.filename.lower().endswith(".pdf"):

            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "result": None,
                    "error": "Only PDF files are allowed."
                }
            )

        # Read file bytes
        file_bytes = await file.read()

        # Check size (10 MB)
        if len(file_bytes) > 10 * 1024 * 1024:

            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "result": None,
                    "error": "PDF size should be below 10 MB."
                }
            )

        # Reset pointer
        await file.seek(0)

        # Save PDF
        file_path = os.path.join(
            UPLOAD_FOLDER,
            file.filename
        )

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Read PDF
        pdf = fitz.open(file_path)

        text = ""

        for page in pdf:
            text += page.get_text()

        pdf.close()

        if text.strip() == "":

            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "result": None,
                    "error": "No readable text found. Scanned PDFs are not supported yet."
                }
            )

        prompt = f"""
You are an expert AI Resume Analyzer.

Extract resume details.

Return ONLY valid JSON.

{{
  "Name":"",
  "Email":"",
  "Phone":"",
  "Skills":[],
  "Education":[],
  "Projects":[],
  "Certifications":[],
  "Languages":[],
  "ResumeScore":0,
  "ATSScore":0,
  "Strengths":[],
  "Suggestions":[]
}}

Resume:

{text}
"""

        response = client.models.generate_content(
            model="models/gemini-3.5-flash",
            contents=prompt
        )

        result_text = response.text.strip()

        result_text = re.sub(
            r"```json|```",
            "",
            result_text
        ).strip()

        try:

            result = json.loads(result_text)

        except:

            result = {
                "Name": None,
                "Email": None,
                "Phone": None,
                "Skills": [],
                "Education": [],
                "Projects": [],
                "Certifications": [],
                "Languages": [],
                "ResumeScore": 0,
                "ATSScore": 0,
                "Strengths": [],
                "Suggestions": []
            }

        json_path = os.path.join(
            OUTPUT_FOLDER,
            "resume_data.json"
        )

        with open(json_path, "w", encoding="utf-8") as f:

            json.dump(
                result,
                f,
                indent=4,
                ensure_ascii=False
            )

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "result": result,
                "error": None
            }
        )

    except Exception as e:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "result": None,
                "error": str(e)
            }
        )
# -----------------------------
# Download JSON
# -----------------------------
@app.get("/download-json")
async def download_json():

    json_path = os.path.join(
        OUTPUT_FOLDER,
        "resume_data.json"
    )

    if not os.path.exists(json_path):

        return {
            "message": "No resume data found."
        }

    return FileResponse(
        path=json_path,
        media_type="application/json",
        filename="resume_data.json"
    )


# -----------------------------
# Download PDF Report
# -----------------------------
@app.get("/download-pdf")
async def download_pdf():

    json_path = os.path.join(
        OUTPUT_FOLDER,
        "resume_data.json"
    )

    if not os.path.exists(json_path):

        return {
            "message": "Resume data not found."
        }

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pdf_path = os.path.join(
        OUTPUT_FOLDER,
        "resume_report.pdf"
    )

    doc = SimpleDocTemplate(pdf_path)

    styles = getSampleStyleSheet()

    story = []

    # -----------------------------
    # Title
    # -----------------------------
    story.append(
        Paragraph(
            "<b>SmartStruct AI Resume Report</b>",
            styles["Title"]
        )
    )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # -----------------------------
    # Personal Details
    # -----------------------------
    story.append(
        Paragraph(
            f"<b>Name:</b> {data.get('Name','N/A')}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Email:</b> {data.get('Email','N/A')}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Phone:</b> {data.get('Phone','N/A')}",
            styles["Normal"]
        )
    )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # -----------------------------
    # Resume Score
    # -----------------------------
    story.append(
        Paragraph(
            "<b>Resume Score</b>",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"{data.get('ResumeScore',0)}/100",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            "<b>ATS Score</b>",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"{data.get('ATSScore',0)}/100",
            styles["Normal"]
        )
    )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # -----------------------------
    # Skills
    # -----------------------------
    story.append(
        Paragraph(
            "<b>Skills</b>",
            styles["Heading2"]
        )
    )

    for skill in data.get("Skills", []):

        story.append(
            Paragraph(
                f"• {skill}",
                styles["Normal"]
            )
        )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # -----------------------------
    # Education
    # -----------------------------
    story.append(
        Paragraph(
            "<b>Education</b>",
            styles["Heading2"]
        )
    )

    for edu in data.get("Education", []):

        story.append(
            Paragraph(
                f"• {edu}",
                styles["Normal"]
            )
        )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # -----------------------------
    # Projects
    # -----------------------------
    story.append(
        Paragraph(
            "<b>Projects</b>",
            styles["Heading2"]
        )
    )

    for project in data.get("Projects", []):

        story.append(
            Paragraph(
                f"• {project}",
                styles["Normal"]
            )
        )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # -----------------------------
    # Certifications
    # -----------------------------
    story.append(
        Paragraph(
            "<b>Certifications</b>",
            styles["Heading2"]
        )
    )

    for cert in data.get("Certifications", []):

        story.append(
            Paragraph(
                f"• {cert}",
                styles["Normal"]
            )
        )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # -----------------------------
    # Languages
    # -----------------------------
    story.append(
        Paragraph(
            "<b>Languages</b>",
            styles["Heading2"]
        )
    )

    for lang in data.get("Languages", []):

        story.append(
            Paragraph(
                f"• {lang}",
                styles["Normal"]
            )
        )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # -----------------------------
    # Strengths
    # -----------------------------
    story.append(
        Paragraph(
            "<b>Strengths</b>",
            styles["Heading2"]
        )
    )

    for item in data.get("Strengths", []):

        story.append(
            Paragraph(
                f"• {item}",
                styles["Normal"]
            )
        )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # -----------------------------
    # Suggestions
    # -----------------------------
    story.append(
        Paragraph(
            "<b>Suggestions</b>",
            styles["Heading2"]
        )
    )

    for item in data.get("Suggestions", []):

        story.append(
            Paragraph(
                f"• {item}",
                styles["Normal"]
            )
        )

    # Generate PDF
    doc.build(story)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="SmartStruct_AI_Report.pdf"
    )