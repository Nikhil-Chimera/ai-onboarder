"""
Type definitions for AI-Onboarder
"""

from typing import Literal, Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# Status types
ProjectStatus = Literal['pending', 'scanning', 'generating', 'ready', 'error']
DocType = Literal[
    'overview',        # Platform Overview
    'how_it_works',    # How It Works
    'training',        # Employee Training
    'terms',           # Terms & Features
    'user_journeys',   # User Journeys
    'troubleshooting', # Troubleshooting
    'custom'           # Custom documents
]
VideoStatus = Literal['pending', 'generating', 'ready', 'error']

# Database models
@dataclass
class Project:
    id: str
    github_url: str
    commit_sha: str
    status: ProjectStatus
    project_md: Optional[str]
    created_at: str
    repo_name: str
    error_message: Optional[str] = None

@dataclass
class Document:
    id: str
    project_id: str
    type: DocType
    title: str
    content: str
    diagram_url: Optional[str]
    created_at: str

@dataclass
class Video:
    id: str
    document_id: str
    status: VideoStatus
    video_url: Optional[str]
    transcript: Optional[str]
    storyboard: Optional[Dict[str, Any]]
    created_at: str
    error_message: Optional[str] = None

@dataclass
class Message:
    role: Literal['user', 'assistant']
    content: str
    citations: Optional[List[Dict[str, Any]]] = None

@dataclass
class RepoInfo:
    owner: str
    repo: str
    branch: str
    commit_sha: str

# Tool result types
@dataclass
class TreeEntry:
    path: str
    type: Literal['file', 'directory']
    size: int

@dataclass
class GrepHit:
    path: str
    line_no: int
    excerpt: str
