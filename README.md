# 🤖 SmartStruct AI

AI-Powered Resume Parser & ATS Analyzer built using FastAPI and Google Gemini AI.

---

## 📌 Overview

SmartStruct AI extracts structured information from resumes and provides AI-powered insights, including Resume Score, ATS Score, strengths, and improvement suggestions.

---

## 🚀 Features

- 📄 Upload PDF resumes
- 🤖 AI-powered resume parsing
- 👤 Extract personal information
- 💻 Extract skills
- 🎓 Extract education
- 📂 Extract projects
- 📜 Extract certifications
- 🌍 Extract languages
- 📊 Resume Score
- 🎯 ATS Score
- ✅ Strength Analysis
- 💡 AI Suggestions
- 📥 Download JSON report
- 📄 Download PDF report
- 🎨 Modern responsive UI

---

## 🛠 Tech Stack

- Python
- FastAPI
- Google Gemini API
- PyMuPDF
- HTML
- CSS
- JavaScript
- Jinja2
- ReportLab

---

## 📂 Project Structure

```text
SmartStruct-AI/
│
├── app/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
├── uploads/
├── output/
├── README.md
├── requirements.txt
└── .gitignore
```

---

## ⚙ Installation

Clone the repository

```bash
git clone https://github.com/yourusername/SmartStruct-AI.git
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file

```env
GEMINI_API_KEY=YOUR_API_KEY
```

Run the project

```bash
uvicorn app.main:app --reload
```

Open

```
http://127.0.0.1:8000
```

---

## 📸 Screenshots

(Add screenshots here after deployment.)

---

## 🔮 Future Improvements

- OCR support
- Resume comparison
- Job Description Matching
- Skill Gap Analysis
- AI Interview Preparation

---

## 📄 License

MIT License

---

Made with ❤️ using FastAPI & Gemini AI