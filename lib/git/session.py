"""
Session manager for reusing cloned repositories in chat sessions
"""

import os
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass

from lib.git.clone import clone_repository, cleanup_repository
from lib.logger import create_logger

log = create_logger('SESSION')

@dataclass
class Session:
    session_id: str
    project_id: str
    repo_path: str
    created_at: float
    last_accessed: float

# Global session storage - keyed by github_url to prevent cross-contamination
_sessions: Dict[str, Session] = {}
SESSION_TIMEOUT = 3600  # 1 hour

def _get_session_key(github_url: str, project_id: str) -> str:
    """Generate a unique session key based on github_url"""
    import hashlib
    # Use github_url to ensure different repos get different sessions
    url_hash = hashlib.md5(github_url.encode()).hexdigest()[:8]
    return f"{url_hash}_{project_id}"

def get_or_create_session(project_id: str, github_url: str, session_id: Optional[str] = None) -> Session:
    """
    Get an existing session or create a new one
    
    Reuses cloned repositories to avoid repeated cloning
    CRITICAL: Sessions are keyed by github_url to prevent different repos from sharing sessions
    """
    import uuid
    
    # Generate session key based on github_url
    session_key = _get_session_key(github_url, project_id)
    
    log.info(f'Session lookup for project {project_id[:8]}... (key: {session_key})')
    log.info(f'GitHub URL: {github_url}')
    
    # Check if we have an existing session for THIS specific github_url + project_id
    if session_key in _sessions:
        session = _sessions[session_key]
        
        # Validate session is still valid and repo path exists
        if time.time() - session.created_at < SESSION_TIMEOUT:
            if os.path.exists(session.repo_path):
                session.last_accessed = time.time()
                log.info(f'✅ Reusing valid session (repo exists at {session.repo_path})')
                return session
            else:
                log.warning(f'⚠️ Session repo path no longer exists: {session.repo_path}')
                # Clean up invalid session
                del _sessions[session_key]
        else:
            # Session expired, clean it up
            log.info(f'Session expired, cleaning up')
            cleanup_session(session_key)
    
    # No valid session found - create new one
    log.info(f'🔄 Creating NEW session for {github_url}')
    log.info(f'Cloning repository...')
    repo_path, repo_info = clone_repository(github_url)
    log.info(f'✅ Repository cloned to: {repo_path}')
    
    new_session_id = str(uuid.uuid4())
    session = Session(
        session_id=new_session_id,
        project_id=project_id,
        repo_path=repo_path,
        created_at=time.time(),
        last_accessed=time.time()
    )
    
    _sessions[session_key] = session
    log.info(f'✅ Session created with key: {session_key}')
    log.info(f'Total active sessions: {len(_sessions)}')
    
    return session

def cleanup_session(session_key: str):
    """Clean up a session and its cloned repository"""
    if session_key in _sessions:
        session = _sessions[session_key]
        log.info(f'Cleaning up session: {session_key}')
        if os.path.exists(session.repo_path):
            cleanup_repository(session.repo_path)
        else:
            log.warning(f'Repo path already gone: {session.repo_path}')
        del _sessions[session_key]
        log.info(f'✅ Session cleaned up')

def cleanup_old_sessions():
    """Clean up expired sessions"""
    current_time = time.time()
    expired_sessions = [
        skey for skey, session in _sessions.items()
        if current_time - session.last_accessed > SESSION_TIMEOUT
    ]
    
    for skey in expired_sessions:
        cleanup_session(skey)
    
    if expired_sessions:
        log.info(f'Cleaned up {len(expired_sessions)} expired sessions')

def get_session_info() -> Dict[str, Any]:
    """Get information about active sessions for debugging"""
    return {
        'total_sessions': len(_sessions),
        'sessions': [
            {
                'key': key,
                'project_id': session.project_id,
                'repo_path': session.repo_path,
                'exists': os.path.exists(session.repo_path),
                'age_seconds': time.time() - session.created_at
            }
            for key, session in _sessions.items()
        ]
    }
