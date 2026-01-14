# 🧠 AI-Onboarder

> **Transform GitHub repositories into comprehensive onboarding documentation with AI-powered analysis, interactive Q&A, and automated video generation.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-blue.svg)](https://ai.google.dev)

---

## 📋 Table of Contents

- [What is AI-Onboarder?](#-what-is-ai-onboarder)
- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
- [Architecture Overview](#-architecture-overview)
- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [API & Components](#-api--components)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## 🎯 What is AI-Onboarder?

AI-Onboarder is an intelligent system that analyzes GitHub repositories and automatically generates comprehensive onboarding materials for new team members and customer support staff. Instead of manually reading through code, your team can:

- **Get instant insights** into any codebase through AI-powered analysis
- **Generate custom documentation** for different audiences (technical, support, training)
- **Create training videos** automatically from documentation
- **Ask questions** about the codebase using an intelligent chatbot

### Use Cases

- 🎓 **Employee Onboarding**: Generate training materials for new hires
- 💼 **Customer Support**: Create troubleshooting guides from codebases
- 📚 **Documentation**: Automatically document platform features
- 🎥 **Training Videos**: Convert docs into engaging video presentations
- 💬 **Knowledge Base**: Interactive Q&A about your codebase

---

## ✨ Key Features

### 1. 🔍 **Intelligent Repository Analysis**
- Clones and analyzes any public GitHub repository
- Deep code exploration using unlimited tool calls
- Understands architecture, dependencies, and relationships
- Generates comprehensive `PROJECT.md` overview

### 2. 📝 **Multi-Format Documentation Generation**
Generate specialized documents for different needs:
- **Platform Overview** - High-level product understanding
- **How It Works** - Technical implementation details
- **Employee Training** - Support team onboarding
- **Terms & Features** - Glossary and feature explanations
- **User Journeys** - End-to-end user flows
- **Troubleshooting Guide** - Common issues and solutions
- **Custom Documents** - Any specific documentation need

### 3. 🎥 **Automated Video Generation**
- Converts documentation into video storyboards
- Generates 7-10 slide presentations
- AI-powered voiceovers using text-to-speech
- Creates images from text descriptions
- Produces MP4 videos ready for training

### 4. 💬 **Interactive Q&A Chat**
- Ask questions about the codebase in natural language
- Get detailed answers with file references
- Searches entire repository for relevant code
- Provides context-aware responses

### 5. 🗄️ **Project Management**
- Track multiple repositories
- Manage document versions
- Monitor video generation status
- SQLite database for data persistence

---

## 🔄 How It Works

### The AI-Onboarder Pipeline

```
┌─────────────────┐
│  GitHub Repo    │
│   (Input URL)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  1. Clone Repo  │◄─── Git Session Manager
│  & Analyze      │     (Persistent repos)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. Mapper      │◄─── Gemini AI Agent
│  Agent Creates  │     + Repo Tools
│  PROJECT.md     │     (explore codebase)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. Doc Agents  │◄─── Specialized agents
│  Generate       │     for each doc type
│  Documentation  │
└────────┬────────┘
         │
         ├─────────────────────┐
         ▼                     ▼
┌─────────────────┐   ┌──────────────────┐
│  4. Video       │   │  5. Q&A Agent    │
│  Generation     │   │  Interactive     │
│  (Storyboard +  │   │  Chat            │
│   TTS + Images) │   │                  │
└─────────────────┘   └──────────────────┘
         │                     │
         ▼                     ▼
┌─────────────────────────────────────┐
│      Streamlit Web Interface        │
│   (View, Download, Interact)        │
└─────────────────────────────────────┘
```

### Step-by-Step Breakdown

#### **Step 1: Repository Cloning & Session Management**
```python
# lib/git/session.py
session = get_or_create_session(project_id, github_url)
# - Creates unique workspace for each project
# - Persists repositories for repeated analysis
# - Manages clone operations efficiently
```

#### **Step 2: Intelligent Mapping**
```python
# lib/agents/mapper.py - MapperAgent
# - Explores repository structure recursively
# - Reads configuration files (package.json, requirements.txt, etc.)
# - Analyzes code patterns and dependencies
# - Generates comprehensive PROJECT.md summary
```

**Mapper Agent Capabilities:**
- 🌳 List directory trees at any depth
- 📖 Read entire files without truncation
- 🔍 Search across all files using patterns
- 🔗 Trace dependencies and imports
- 📊 Understand architecture from code

#### **Step 3: Specialized Documentation Agents**
```python
# lib/agents/doc_agents.py - DocAgents
# Each agent is an expert in creating specific documentation types
```

**Available Document Types:**

| Document Type | Purpose | Target Audience |
|--------------|---------|-----------------|
| `overview` | Platform Overview | All stakeholders |
| `how_it_works` | Technical Implementation | Developers |
| `training` | Employee Training | Support teams |
| `terms` | Terms & Features | Support/Sales |
| `user_journeys` | User Flows | Product/UX teams |
| `troubleshooting` | Issue Resolution | Support teams |

**How Doc Agents Work:**
1. Receive `PROJECT.md` as context
2. Use repository tools to explore specific areas
3. Generate targeted documentation with citations
4. Include diagrams and code references

#### **Step 4: Video Generation Pipeline**
```python
# lib/agents/video_agent.py + lib/video/generator.py
```

**Video Creation Process:**

1. **Storyboard Generation** (Gemini AI)
   - Converts documentation into 7-10 slides
   - Creates engaging narration scripts
   - Generates image prompts for visuals

2. **Asset Creation**
   - Text-to-Speech for voiceovers (gTTS)
   - AI-generated images for each slide (Pollinations.ai)
   - Background music and transitions

3. **Video Assembly** (MoviePy)
   - Combines images, audio, and effects
   - Creates professional MP4 output
   - Saves to `public/videos/`

#### **Step 5: Interactive Q&A**
```python
# lib/agents/qa_agent.py - QAAgent
```

**Chat Capabilities:**
- 🔎 Searches entire codebase for answers
- 📝 Reads relevant files completely
- 🔗 Cross-references multiple files
- 📍 Provides file:line citations
- 💡 Explains complex concepts clearly

---

## 🏗️ Architecture Overview

### System Components

```
AI-Onboarder/
│
├── 🌐 Web Layer (Streamlit)
│   ├── app.py                 # Main application entry
│   ├── pages/
│   │   ├── home.py           # Repository submission
│   │   └── project_view.py   # Project dashboard
│   └── components/
│       └── chat_interface.py # Q&A chat UI
│
├── 🤖 AI Agents Layer
│   ├── lib/agents/
│   │   ├── base.py           # BaseAgent (Gemini integration)
│   │   ├── mapper.py         # MapperAgent (repo analysis)
│   │   ├── doc_agents.py     # DocAgents (documentation)
│   │   ├── qa_agent.py       # QAAgent (chat)
│   │   └── video_agent.py    # VideoAgent (storyboards)
│
├── 🔧 Tools Layer
│   ├── lib/tools/
│   │   └── repo_tools.py     # Repository exploration tools
│   ├── lib/git/
│   │   ├── clone.py          # Git operations
│   │   └── session.py        # Session management
│   └── lib/video/
│       ├── generator.py      # Video creation
│       ├── tts.py           # Text-to-speech
│       └── ffmpeg.py        # Media processing
│
└── 💾 Data Layer
    ├── lib/database.py       # SQLite operations
    ├── lib/types.py          # Data models
    └── ai_onboarder.db       # SQLite database
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | Streamlit | Interactive web interface |
| **AI Model** | Google Gemini 2.0 Flash | Code analysis & content generation |
| **Version Control** | GitPython | Repository cloning & management |
| **Database** | SQLite | Project & document storage |
| **Media Processing** | MoviePy, FFmpeg | Video generation |
| **Text-to-Speech** | gTTS | Voice generation |
| **Image Generation** | Pollinations.ai | Slide visuals |

### Data Models

#### **Project**
```python
@dataclass
class Project:
    id: str                    # UUID
    github_url: str            # Repository URL
    repo_name: str             # owner/repo
    commit_sha: str            # Git commit
    status: ProjectStatus      # pending/cloning/generating/ready/error
    project_md: Optional[str]  # Generated overview
    error_message: Optional[str]
    created_at: str
```

#### **Document**
```python
@dataclass
class Document:
    id: str
    project_id: str
    type: DocType              # overview/training/troubleshooting/etc.
    title: str
    content: str               # Generated markdown
    diagram_url: Optional[str]
    created_at: str
```

#### **Video**
```python
@dataclass
class Video:
    id: str
    document_id: str
    status: VideoStatus        # pending/generating/ready/error
    video_url: Optional[str]   # Path to MP4
    transcript: Optional[str]
    storyboard: Optional[str]  # JSON storyboard
    error_message: Optional[str]
    created_at: str
```

---

## 🚀 Installation & Setup

### Prerequisites

- **Python 3.10 or higher**
- **Git** (for cloning repositories)
- **FFmpeg** (for video generation)
- **Google Gemini API Key** ([Get one free](https://ai.google.dev))

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/AI-Onboarder.git
cd AI-Onboarder
```

### Step 2: Create Virtual Environment

**Windows:**
```powershell
python -m venv myenv
.\myenv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv myenv
source myenv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install FFmpeg

**Windows (Chocolatey):**
```powershell
choco install ffmpeg
```

**Mac (Homebrew):**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### Step 5: Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

3. Get your free API key from [Google AI Studio](https://ai.google.dev)

### Step 6: Initialize Database

The database will be created automatically on first run, but you can verify:

```bash
python -c "from lib.database import init_db; init_db()"
```

### Step 7: Launch Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

---

## 📖 Usage Guide

### Quick Start: Analyze Your First Repository

#### 1. **Submit a Repository**

![Home Page](https://via.placeholder.com/800x400/4A90E2/FFFFFF?text=Home+Page+Screenshot)

- Open AI-Onboarder in your browser
- Enter a GitHub URL (e.g., `https://github.com/strapi/strapi`)
- Click **"Analyze Repository"**

#### 2. **Wait for Analysis**

The system will:
- ✅ Clone the repository
- 🔍 Analyze the codebase
- 📝 Generate PROJECT.md overview
- 🎯 Status updates in real-time

**Typical Analysis Time:** 2-5 minutes depending on repo size

#### 3. **View Project Dashboard**

Once ready, you'll see:
- 📊 **Overview Tab** - PROJECT.md summary
- 📚 **Documents Tab** - Generate custom docs
- 🎥 **Videos Tab** - Create training videos
- 💬 **Chat Tab** - Ask questions about the code

### Generating Documentation

#### **Generate a Document**

1. Navigate to the **Documents** tab
2. Click **"➕ Generate New Document"**
3. Select document type:
   - Platform Overview
   - How It Works
   - Employee Training
   - Terms & Features
   - User Journeys
   - Troubleshooting Guide
   - Custom (with your own title)
4. Click **"Generate"**
5. Wait 2-4 minutes for AI generation
6. View and download the markdown

#### **Document Structure**

Each generated document includes:
- Clear headings and sections
- Code references with file paths
- ASCII diagrams where relevant
- Actionable insights
- Support-focused content

### Creating Training Videos

#### **Generate a Video from Documentation**

1. Generate a document first (or use existing)
2. Navigate to the **Videos** tab
3. Click **"🎬 Generate Video"** next to any document
4. Wait 5-10 minutes for video creation
5. Watch inline or download MP4

#### **Video Format**

- **Duration:** 5-8 minutes
- **Slides:** 7-10 professional slides
- **Voiceover:** AI-generated narration
- **Visuals:** Relevant images and diagrams
- **Quality:** 1080p MP4

#### **Storyboard Preview**

View the JSON storyboard before video generation:
```json
{
  "slides": [
    {
      "title": "Introduction to Platform",
      "bullets": ["Key feature 1", "Key feature 2"],
      "imagePrompt": "Professional diagram showing...",
      "voiceover": "Welcome to this training video..."
    }
  ]
}
```

### Interactive Chat (Q&A)

#### **Ask Questions About the Codebase**

1. Navigate to the **Chat** tab
2. Type your question in natural language
3. Press Enter or click Send
4. Get detailed answers with code references

#### **Example Questions**

```
"How does authentication work?"
"What database does this project use?"
"Explain the API architecture"
"Where is the user login function?"
"What are the main dependencies?"
"How do I set up the development environment?"
```

#### **Chat Features**

- 🔍 **Deep Code Search** - Searches entire repository
- 📝 **Complete File Reading** - No truncation
- 🔗 **File Citations** - Links to specific files and lines
- 💡 **Contextual Understanding** - Follows code relationships
- 📚 **Memory** - Remembers conversation context

---

## 📁 Project Structure

### Complete Directory Layout

```
AI-Onboarder/
│
├── 📄 app.py                      # Main Streamlit application
├── 📄 requirements.txt            # Python dependencies
├── 📄 .env.example                # Environment template
├── 📄 .env                        # Your API keys (git-ignored)
├── 📄 .gitignore                  # Git ignore rules
├── 📄 README.md                   # This file
│
├── 📂 components/                 # UI Components
│   ├── __init__.py
│   └── chat_interface.py          # Chat widget
│
├── 📂 pages/                      # Streamlit pages
│   ├── __init__.py
│   ├── home.py                    # Repository submission page
│   └── project_view.py            # Project dashboard page
│
├── 📂 lib/                        # Core library
│   ├── __init__.py
│   ├── database.py                # SQLite operations
│   ├── logger.py                  # Logging utilities
│   ├── types.py                   # Data models & types
│   │
│   ├── 📂 agents/                 # AI Agents
│   │   ├── __init__.py
│   │   ├── base.py                # BaseAgent class
│   │   ├── mapper.py              # Repository mapper
│   │   ├── doc_agents.py          # Documentation generators
│   │   ├── qa_agent.py            # Q&A chatbot
│   │   └── video_agent.py         # Storyboard generator
│   │
│   ├── 📂 git/                    # Git operations
│   │   ├── __init__.py
│   │   ├── clone.py               # Repository cloning
│   │   └── session.py             # Session management
│   │
│   ├── 📂 tools/                  # Agent tools
│   │   ├── __init__.py
│   │   └── repo_tools.py          # Repository exploration
│   │
│   └── 📂 video/                  # Video generation
│       ├── __init__.py
│       ├── generator.py           # Video assembly
│       ├── tts.py                 # Text-to-speech
│       └── ffmpeg.py              # FFmpeg utilities
│
├── 📂 public/                     # Static files
│   └── videos/                    # Generated videos (MP4)
│
├── 📂 myenv/                      # Virtual environment (git-ignored)
│
└── 📊 ai_onboarder.db             # SQLite database (git-ignored)
```

### Key Files Explained

#### **Core Application Files**

- **`app.py`** - Entry point, initializes Streamlit app, routes between pages
- **`pages/home.py`** - Home page with repo submission and project list
- **`pages/project_view.py`** - Project detail view with tabs for docs, videos, chat

#### **AI Agent Files**

- **`lib/agents/base.py`** - Base class for all agents, handles Gemini API
- **`lib/agents/mapper.py`** - Analyzes repos and creates PROJECT.md
- **`lib/agents/doc_agents.py`** - Specialized agents for each doc type
- **`lib/agents/qa_agent.py`** - Handles interactive chat questions
- **`lib/agents/video_agent.py`** - Generates video storyboards

#### **Tool Files**

- **`lib/tools/repo_tools.py`** - Provides tools for agents to explore repositories
  - `listTree()` - List directory contents
  - `readFile()` - Read file contents
  - `search()` - Search for patterns

#### **Infrastructure Files**

- **`lib/database.py`** - All SQLite CRUD operations
- **`lib/git/session.py`** - Manages persistent repository sessions
- **`lib/video/generator.py`** - Assembles videos from storyboards

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Google Gemini API Key (Required)
GOOGLE_API_KEY=your_api_key_here

# Optional: Custom model configuration
# GEMINI_MODEL=gemini-2.0-flash-exp

# Optional: Database path
# DB_PATH=custom_path/ai_onboarder.db
```

### Gemini API Configuration

The project uses **Google Gemini 2.0 Flash** by default:
- Free tier: 15 requests per minute
- Excellent for code analysis
- Supports large context windows

**To get an API key:**
1. Visit [Google AI Studio](https://ai.google.dev)
2. Sign in with Google account
3. Create a new API key
4. Copy to `.env` file

### Customizing Agent Behavior

#### **Modify System Prompts**

Edit prompts in [`lib/agents/doc_agents.py`](lib/agents/doc_agents.py):

```python
DOC_AGENT_PROMPTS = {
    'custom_type': """
        Your custom system prompt here...
        Define how the agent should behave...
    """
}
```

#### **Add New Document Types**

1. Add to [`lib/types.py`](lib/types.py):
   ```python
   class DocType:
       CUSTOM_TYPE = 'custom_type'
   ```

2. Add prompt to [`lib/agents/doc_agents.py`](lib/agents/doc_agents.py)

3. Add title to [`pages/project_view.py`](pages/project_view.py):
   ```python
   DOC_TITLES = {
       'custom_type': 'Custom Type Title'
   }
   ```

### Video Generation Settings

Modify video parameters in [`lib/video/generator.py`](lib/video/generator.py):

```python
# Video resolution
VIDEO_SIZE = (1920, 1080)  # 1080p

# Slide duration
SLIDE_DURATION = 10  # seconds per slide

# Text-to-speech settings
TTS_LANG = 'en'  # Language code
TTS_SLOW = False  # Slower speech
```

---

## 🔌 API & Components

### Database API

#### **Project Operations**

```python
from lib.database import (
    create_project,
    get_project,
    get_all_projects,
    update_project,
    update_project_status,
    delete_project
)

# Create project
project = Project(
    id=str(uuid.uuid4()),
    github_url="https://github.com/owner/repo",
    repo_name="owner/repo",
    status="pending",
    created_at=datetime.now().isoformat()
)
create_project(project)

# Get project
project = get_project(project_id)

# Update status
update_project_status(project_id, 'ready')
```

#### **Document Operations**

```python
from lib.database import (
    create_document,
    get_document,
    get_documents_by_project,
    get_document_by_project_and_type
)

# Create document
doc = Document(
    id=str(uuid.uuid4()),
    project_id=project_id,
    type='overview',
    title='Platform Overview',
    content='# Generated content...',
    created_at=datetime.now().isoformat()
)
create_document(doc)

# Get all documents for a project
docs = get_documents_by_project(project_id)
```

#### **Video Operations**

```python
from lib.database import (
    create_video,
    get_videos_by_document,
    update_video_status
)

# Create video
video = Video(
    id=str(uuid.uuid4()),
    document_id=doc_id,
    status='pending',
    created_at=datetime.now().isoformat()
)
create_video(video)

# Update video status
update_video_status(video_id, 'ready', video_url='public/videos/xyz.mp4')
```

### Agent API

#### **Using MapperAgent**

```python
from lib.agents import MapperAgent
from lib.tools import create_repo_tools

# Create tools for repository
repo_tools = create_repo_tools('/path/to/repo')

# Create and run mapper
mapper = MapperAgent(repo_tools)
project_md = mapper.analyze_repository()
```

#### **Using DocAgents**

```python
from lib.agents import create_doc_agents

# Create all doc agents
doc_agents = create_doc_agents(repo_tools)

# Generate specific document
agent = doc_agents['training']
content = agent.generate_doc(
    project_context=project_md,
    title='Employee Training Guide'
)
```

#### **Using QAAgent**

```python
from lib.agents import QAAgent

# Create Q&A agent
qa_agent = QAAgent(repo_tools)

# Ask question
answer = qa_agent.answer_question(
    question="How does authentication work?",
    chat_history=[]
)
```

### Repository Tools API

```python
from lib.tools import create_repo_tools

# Create tools
tools = create_repo_tools('/path/to/repo')

# List directory
contents = tools.listTree('src/')

# Read file
content = tools.readFile('src/main.py')

# Search for pattern
results = tools.search('function', file_pattern='*.py')
```

---

## 🐛 Troubleshooting

### Common Issues & Solutions

#### **1. "GOOGLE_API_KEY not found" Error**

**Problem:** API key not configured

**Solution:**
```bash
# Create .env file
cp .env.example .env

# Edit .env and add your key
GOOGLE_API_KEY=your_key_here
```

#### **2. "FFmpeg not found" Error**

**Problem:** FFmpeg not installed

**Solution:**
```bash
# Windows
choco install ffmpeg

# Mac
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

#### **3. Repository Cloning Fails**

**Problem:** Git authentication or network issues

**Solution:**
- Ensure repository URL is correct and public
- Check internet connection
- Try with a different repository
- Check logs in terminal for details

#### **4. Video Generation Stuck**

**Problem:** Long processing time or failure

**Solution:**
- Check FFmpeg installation: `ffmpeg -version`
- Verify free disk space in `public/videos/`
- Check logs for error messages
- Try with shorter documentation

#### **5. Gemini API Rate Limit**

**Problem:** "429 Too Many Requests"

**Solution:**
- Free tier: 15 requests/minute
- Wait 60 seconds between large requests
- Consider upgrading to paid tier
- Reduce document complexity

#### **6. Database Lock Errors**

**Problem:** "Database is locked"

**Solution:**
```python
# Close all connections
import sqlite3
conn = sqlite3.connect('ai_onboarder.db')
conn.close()

# Or delete and reinitialize
# rm ai_onboarder.db
# python -c "from lib.database import init_db; init_db()"
```

### Debug Mode

Enable verbose logging:

```python
# lib/logger.py - Change log level
import logging
logging.basicConfig(level=logging.DEBUG)
```

View detailed logs in terminal while running:
```bash
streamlit run app.py --logger.level=debug
```

### Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review terminal logs for error messages
3. Verify all dependencies are installed
4. Check [GitHub Issues](https://github.com/yourusername/AI-Onboarder/issues)
5. Open a new issue with:
   - Error message
   - Steps to reproduce
   - System info (OS, Python version)

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. Fork the repository
2. Create a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
   ```bash
   git commit -m "Add amazing feature"
   ```
6. Push to your fork
   ```bash
   git push origin feature/amazing-feature
   ```
7. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to functions
- Keep functions focused and small

### Testing

Before submitting:
- Test with multiple repositories
- Verify all document types generate
- Test video generation end-to-end
- Check chat functionality

---

## 📊 Performance & Limitations

### Performance Metrics

| Operation | Typical Time | Notes |
|-----------|-------------|-------|
| Repository cloning | 30s - 2min | Depends on repo size |
| PROJECT.md generation | 1-3 minutes | Small repos faster |
| Document generation | 2-4 minutes | Varies by complexity |
| Video generation | 5-10 minutes | Most time-consuming |
| Chat response | 5-15 seconds | Per question |

### Current Limitations

- **Public Repositories Only** - No private repo support yet
- **English Language** - Best results with English codebases
- **Large Repositories** - May timeout on massive repos (>100MB)
- **API Rate Limits** - Free tier has request limits
- **Video Quality** - AI-generated images may vary

### Roadmap

Future enhancements planned:
- [ ] Private repository support with authentication
- [ ] Multiple language support
- [ ] Parallel document generation
- [ ] Custom video templates
- [ ] Export to PDF/Word
- [ ] Team collaboration features
- [ ] API endpoint for integrations

---

## 🙏 Acknowledgments

- **Google Gemini** - Powerful AI for code analysis
- **Streamlit** - Beautiful web framework
- **MoviePy** - Video generation library
- **FFmpeg** - Media processing
- **Open Source Community** - Inspiration and tools
