"""
Database operations using SQLite
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from lib.types import Project, Document, Video, ProjectStatus, DocType, VideoStatus
from lib.logger import create_logger

log = create_logger('DB')

DB_PATH = 'ai_onboarder.db'

def get_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    log.info(f'Initializing database at {DB_PATH}')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            github_url TEXT NOT NULL,
            repo_name TEXT NOT NULL,
            commit_sha TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            project_md TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            diagram_url TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    ''')
    
    # Videos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            video_url TEXT,
            transcript TEXT,
            storyboard TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_document_id ON videos(document_id)')
    
    conn.commit()
    conn.close()
    
    log.info('Database initialized successfully')

# ============================================================================
# PROJECT OPERATIONS
# ============================================================================

def create_project(project: Project) -> Project:
    """Create a new project"""
    log.info(f'Creating project: {project.id} - {project.repo_name}')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO projects (id, github_url, repo_name, commit_sha, status, project_md, error_message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        project.id,
        project.github_url,
        project.repo_name,
        project.commit_sha,
        project.status,
        project.project_md,
        project.error_message,
        project.created_at
    ))
    
    conn.commit()
    conn.close()
    
    return project

def get_project(project_id: str) -> Optional[Project]:
    """Get a project by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return Project(**dict(row))
    return None

def get_all_projects() -> List[Project]:
    """Get all projects"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM projects ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [Project(**dict(row)) for row in rows]

def update_project(project_id: str, updates: Dict[str, Any]) -> Optional[Project]:
    """Update a project"""
    log.info(f'Updating project: {project_id}')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build dynamic update query
    fields = []
    values = []
    
    for key, value in updates.items():
        fields.append(f'{key} = ?')
        values.append(value)
    
    if not fields:
        return get_project(project_id)
    
    values.append(project_id)
    query = f"UPDATE projects SET {', '.join(fields)} WHERE id = ?"
    
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    
    return get_project(project_id)

def update_project_status(project_id: str, status: ProjectStatus, error_message: Optional[str] = None):
    """Update project status"""
    updates = {'status': status}
    if error_message:
        updates['error_message'] = error_message
    update_project(project_id, updates)

# ============================================================================
# DOCUMENT OPERATIONS
# ============================================================================

def create_document(document: Document) -> Document:
    """Create a new document"""
    log.info(f'Creating document: {document.id} - {document.title}')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO documents (id, project_id, type, title, content, diagram_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        document.id,
        document.project_id,
        document.type,
        document.title,
        document.content,
        document.diagram_url,
        document.created_at
    ))
    
    conn.commit()
    conn.close()
    
    return document

def get_document(document_id: str) -> Optional[Document]:
    """Get a document by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return Document(**dict(row))
    return None

def get_documents_by_project(project_id: str) -> List[Document]:
    """Get all documents for a project"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM documents WHERE project_id = ? ORDER BY created_at DESC', (project_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [Document(**dict(row)) for row in rows]

def get_document_by_project_and_type(project_id: str, doc_type: DocType) -> Optional[Document]:
    """Get a specific document type for a project"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT * FROM documents WHERE project_id = ? AND type = ? LIMIT 1',
        (project_id, doc_type)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return Document(**dict(row))
    return None

# ============================================================================
# VIDEO OPERATIONS
# ============================================================================

def create_video(video: Video) -> Video:
    """Create a new video"""
    log.info(f'Creating video: {video.id}')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    storyboard_json = json.dumps(video.storyboard) if video.storyboard else None
    
    cursor.execute('''
        INSERT INTO videos (id, document_id, status, video_url, transcript, storyboard, error_message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        video.id,
        video.document_id,
        video.status,
        video.video_url,
        video.transcript,
        storyboard_json,
        video.error_message,
        video.created_at
    ))
    
    conn.commit()
    conn.close()
    
    return video

def get_videos_by_document(document_id: str) -> List[Video]:
    """Get all videos for a document"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM videos WHERE document_id = ? ORDER BY created_at DESC', (document_id,))
    rows = cursor.fetchall()
    conn.close()
    
    videos = []
    for row in rows:
        data = dict(row)
        # Parse storyboard JSON if present
        if data.get('storyboard'):
            try:
                data['storyboard'] = json.loads(data['storyboard'])
            except (json.JSONDecodeError, TypeError) as e:
                log.warning(f'Failed to parse storyboard JSON: {e}')
                data['storyboard'] = None
        else:
            data['storyboard'] = None
        videos.append(Video(**data))
    
    return videos

def update_video_status(video_id: str, status: VideoStatus, error_message: Optional[str] = None):
    """Update video status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if error_message:
        cursor.execute(
            'UPDATE videos SET status = ?, error_message = ? WHERE id = ?',
            (status, error_message, video_id)
        )
    else:
        cursor.execute('UPDATE videos SET status = ? WHERE id = ?', (status, video_id))
    
    conn.commit()
    conn.close()
