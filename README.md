# 🍎 TeachersAiPet - Teacher Intelligence Platform

> **Empowering educators with AI-driven insights, automation, and comprehensive student management.**

TeachersAiPet (Admin Suite) is a robust, AI-powered backend architecture designed to completely streamline a teacher's workflow. Built with Django and Django REST Framework, it automates everything from generating personalized assignments to tracking behavioral patterns, pacing curriculums, and communicating with parents—all tailored through the power of OpenAI.

---

## 🚀 Key Features

*   **🤖 AI-Powered Content Generation:**
    *   **Dynamic Assignments:** Automatically generate subject-specific, CCSS-aligned assignments with variable AI difficulty levels using GPT-4o.
    *   **Lesson Recommendations:** Receive tailored, AI-crafted lesson plans and teaching strategies based on classroom performance metrics.
    *   **Parent Messages:** Automatically draft personalized, context-aware emails to parents summarizing student progress and behavior.
*   **👥 Comprehensive Student & Group Management:**
    *   Organize students into dynamic groups for targeted learning.
    *   Track individual performance, attendance, and behavioral observations in real-time.
*   **📊 Advanced Analytics & Dashboard:**
    *   Centralized dashboard providing deep statistical insights into classroom engagement and academic growth.
    *   Automated Admin Analysis Reports exported directly as beautiful PDF documents.
*   **📩 Automated Communication & Submissions:**
    *   One-click email delivery of assignments directly to parents with attached PDFs.
    *   Custom, secure frontend portals for students to submit completed assignments dynamically (`/api/assignments/public/{unique_code}/submit`).
    *   Strict security validation to ensure only authorized students submit specific assignments.
*   **🔒 Enterprise-Grade Security:**
    *   Role-based access control (Admin vs. Teacher) secured via SimpleJWT.
    *   Strict rate-limiting and robust cross-origin resource sharing (CORS) configurations.

---

## 🛠️ Technology Stack

**Core Backend:**
*   **Language:** Python 3.x
*   **Framework:** Django 5.0.6
*   **API Architecture:** Django REST Framework (DRF)
*   **Database:** SQLite (Development) / PostgreSQL (Production ready)

**AI & Asynchronous Processing:**
*   **AI Integration:** OpenAI API (`gpt-4o-mini` / `gpt-4o`)
*   **Task Queue:** Celery with Redis broker (for async email and AI tasks)
*   **Caching:** Redis / LocMemCache

**Security & Utilities:**
*   **Authentication:** JWT (JSON Web Tokens) via `djangorestframework-simplejwt`
*   **PDF Generation:** ReportLab (dynamically generating analysis reports and assignments)
*   **File Handling:** Django Media Storage with built-in MultiPart parsers.

---

## 📁 Project Architecture

The architecture is highly modular, splitting distinct business logic into dedicated micro-apps:

*   `adminapp/` - Global administrative controls, AI configuration, and platform usage analytics.
*   `ai_recommendations/` - Core engine for processing LLM requests.
*   `assignmentapp/` - Full lifecycle of assignments (AI generation, PDF export, email delivery, secure student submission).
*   `attendenceapp/` - Daily attendance tracking and reporting.
*   `authapp/` - Secure JWT login, registration, and user profiles.
*   `behaviorapp/` - Logging and analyzing student behavioral trends.
*   `dashboardapp/` - Aggregation of metrics for the teacher dashboard.
*   `feedbackapp/` - AI-driven feedback loops for student work.
*   `groupapp/` - Group creation and assignment targeting.
*   `interventionsapp/` - Identifying at-risk students and planning academic interventions.
*   `lesson_recommendationsapp/` - AI lesson planning based on pacing and historical data.
*   `observationsapp/` - Teacher notes and qualitative student observations.
*   `pacingapp/` - Curriculum pacing and schedule management.
*   `parent_messagesapp/` - Automated parent communication pipelines.
*   `progressapp/` - Academic tracking and progress reports.
*   `studentapp/` - Core student data models and CRUD operations.

---

## ⚙️ Getting Started (Local Development)

### 1. Prerequisites
*   Python 3.10+
*   Redis (for Celery workers)
*   OpenAI API Key

### 2. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd TeachersAiPet

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory (alongside `manage.py`):
```env
DJANGO_SECRET_KEY=your-secure-secret-key-min-32-chars
DJANGO_DEBUG=True
OPENAI_API_KEY=sk-your-openai-key
CELERY_BROKER_URL=redis://localhost:6379/1
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 4. Database Setup & Run
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start the Django development server (Default: port 8000)
python manage.py runserver
```

---

> **Note to Recruiters:** This project demonstrates a strong command of modern backend architecture, RESTful API design, complex database relations, third-party API integration (OpenAI), asynchronous task processing, and file management—all structured within a highly scalable and maintainable Django environment.
