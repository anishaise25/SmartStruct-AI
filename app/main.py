import os
import json
import shutil
import re
import fitz

from pathlib import Path

from dotenv import load_dotenv
from google import genai

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# -----------------------------
# Base Directory
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

# -----------------------------
# Templates
# -----------------------------
templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

# -----------------------------
# Load Gemini API Key
# -----------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found.")

client = genai.Client(api_key=API_KEY)

# -----------------------------
# Project Folders
# -----------------------------
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "output"

UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

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

        # Check PDF extension
        if not file.filename.lower().endswith(".pdf"):
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "result": None,
                    "error": "Only PDF files are allowed."
                }
            )

        # Read uploaded file
        file_bytes = await file.read()

        # Max size = 10 MB
        if len(file_bytes) > 10 * 1024 * 1024:
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "result": None,
                    "error": "PDF size should be below 10 MB."
                }
            )

        # Reset file pointer
        await file.seek(0)

        # Save uploaded PDF
        file_path = UPLOAD_FOLDER / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Read PDF
        pdf = fitz.open(str(file_path))

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

        # Gemini Prompt
        prompt = f"""
You are an expert AI Resume Analyzer.

Analyze the following resume and return ONLY valid JSON.

Schema:

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

        # Gemini Response
        response = client.models.generate_content(
            model="models/gemini-3.5-flash",
            contents=prompt
        )

        result_text = response.text.strip()

        # Remove markdown if present
        result_text = re.sub(
            r"```json|```",
            "",
            result_text
        ).strip()

        # Convert JSON
        try:
            result = json.loads(result_text)

        except Exception:

            result = {
                "Name": "",
                "Email": "",
                "Phone": "",
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

        # Save JSON
        json_path = OUTPUT_FOLDER / "resume_data.json"

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

    json_path = OUTPUT_FOLDER / "resume_data.json"

    if not json_path.exists():

        return {
            "message": "No resume data found."
        }

    return FileResponse(
        path=str(json_path),
        media_type="application/json",
        filename="resume_data.json"
    )
# -----------------------------
# Download PDF Report
# -----------------------------
@app.get("/download-pdf")
async def download_pdf():

    json_path = OUTPUT_FOLDER / "resume_data.json"

    if not json_path.exists():

        return {
            "message": "Resume data not found."
        }

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pdf_path = OUTPUT_FOLDER / "resume_report.pdf"

    doc = SimpleDocTemplate(str(pdf_path))

    styles = getSampleStyleSheet()

    story = []

    # Title
    story.append(
        Paragraph(
            "<b>SmartStruct AI Resume Report</b>",
            styles["Title"]
        )
    )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # Personal Information
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

    # Resume Score
    story.append(
        Paragraph(
            f"<b>Resume Score:</b> {data.get('ResumeScore',0)}/100",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"<b>ATS Score:</b> {data.get('ATSScore',0)}/100",
            styles["Heading2"]
        )
    )

    story.append(Paragraph("<br/>", styles["Normal"]))

    # Helper Function
    def add_section(title, items):

        story.append(
            Paragraph(
                f"<b>{title}</b>",
                styles["Heading2"]
            )
        )

        if items:

            for item in items:
                story.append(
                    Paragraph(
                        f"• {item}",
                        styles["Normal"]
                    )
                )

        else:

            story.append(
                Paragraph(
                    "No Data",
                    styles["Normal"]
                )
            )

        story.append(
            Paragraph("<br/>", styles["Normal"])
        )

    add_section("Skills", data.get("Skills", []))
    add_section("Education", data.get("Education", []))
    add_section("Projects", data.get("Projects", []))
    add_section("Certifications", data.get("Certifications", []))
    add_section("Languages", data.get("Languages", []))
    add_section("Strengths", data.get("Strengths", []))
    add_section("Suggestions", data.get("Suggestions", []))

    doc.build(story)

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename="SmartStruct_AI_Report.pdf"
    )
@app.get("/test")
async def test():
    return {"message": "App is working!"}