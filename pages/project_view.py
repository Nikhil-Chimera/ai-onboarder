"""
Project view page - Documentation, Videos, and Chat interface
"""

import streamlit as st
import uuid
import os
from datetime import datetime
import threading
import asyncio

from lib.database import (
    get_project, get_documents_by_project, create_document,
    get_document_by_project_and_type, create_video, get_videos_by_document,
    update_video_status
)
from lib.types import Document, Video
from lib.git import get_or_create_session
from lib.tools import create_repo_tools
from lib.agents import create_doc_agents, QAAgent
from lib.agents.video_agent import generate_storyboard
from lib.video import generate_video_async
from lib.logger import create_logger

log = create_logger('PROJECT')

# Document type titles
DOC_TITLES = {
    'overview': 'Platform Overview',
    'how_it_works': 'How It Works',
    'training': 'Employee Training',
    'terms': 'Terms & Features',
    'user_journeys': 'User Journeys',
    'troubleshooting': 'Troubleshooting Guide',
    'custom': 'Custom Document'
}

def generate_document_async(project_id: str, doc_type: str, title: str, project_md: str, github_url: str):
    """Generate document in background"""
    try:
        log.info('=' * 80)
        log.info(f'DOCUMENT GENERATION START')
        log.info(f'Project ID: {project_id}')
        log.info(f'Doc Type: {doc_type}')
        log.info(f'GitHub URL: {github_url}')
        log.info('=' * 80)
        
        # Get or create session
        session = get_or_create_session(project_id, github_url)
        
        # Validate session repo path
        if not os.path.exists(session.repo_path):
            raise ValueError(f'Session repo path does not exist: {session.repo_path}')
        
        log.info(f'Using repository at: {session.repo_path}')
        
        # Create tools and agent
        repo_tools = create_repo_tools(session.repo_path)
        doc_agents = create_doc_agents(repo_tools)
        
        # Generate document
        agent = doc_agents.get(doc_type)
        if not agent:
            log.error(f'Unknown document type: {doc_type}')
            return
        
        content = agent.generate_doc(project_md, title)
        
        # Save document
        document = Document(
            id=str(uuid.uuid4()),
            project_id=project_id,
            type=doc_type,
            title=title,
            content=content,
            diagram_url=None,
            created_at=datetime.now().isoformat()
        )
        
        create_document(document)
        log.info(f'Document created: {document.id}')
        
    except Exception as e:
        log.error(f'Document generation failed: {e}')

def generate_video_async_wrapper(video_id: str, document_id: str, document: Document):
    """Generate video in background"""
    try:
        log.info(f'Generating video for document: {document_id}')
        
        # Generate storyboard
        update_video_status(video_id, 'generating')
        storyboard = generate_storyboard(document.title, document.content)
        
        # Generate video with asyncio
        async def gen():
            result = await generate_video_async(video_id, storyboard)
            
            # Update video in database
            from lib.database import get_connection
            import json
            conn = get_connection()
            cursor = conn.cursor()
            
            # Convert storyboard to JSON string
            storyboard_json = json.dumps(storyboard) if storyboard else None
            
            cursor.execute('''
                UPDATE videos 
                SET status = ?, video_url = ?, storyboard = ?
                WHERE id = ?
            ''', ('ready', result['videoUrl'], storyboard_json, video_id))
            
            conn.commit()
            conn.close()
            
            log.info(f'Video ready: {video_id}')
        
        # Run async function
        asyncio.run(gen())
        
    except Exception as e:
        log.error(f'Video generation failed: {e}')
        update_video_status(video_id, 'error', str(e))

def render(navigate_to, project_id: str):
    """Render project view page"""
    
    # Back button
    if st.button('← Back to Projects'):
        navigate_to('home')
    
    # Load project
    project = get_project(project_id)
    
    if not project:
        st.error('Project not found')
        return
    
    if project.status != 'ready':
        st.warning(f'Project is not ready yet. Status: {project.status}')
        return
    
    # Header
    st.title(project.repo_name)
    st.caption(f'Commit: {project.commit_sha[:8]}')
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(['📄 Documents', '🎥 Videos', '💬 Chat'])
    
    with tab1:
        render_documents_tab(project)
    
    with tab2:
        render_videos_tab(project)
    
    with tab3:
        render_chat_tab(project)

def render_documents_tab(project):
    """Render documents tab"""
    
    st.subheader('Documentation')
    
    # Document generation section
    with st.expander('➕ Generate New Document'):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            doc_type = st.selectbox(
                'Document Type',
                options=list(DOC_TITLES.keys()),
                format_func=lambda x: DOC_TITLES[x]
            )
        
        with col2:
            if st.button('Generate', type='primary', use_container_width=True):
                # Check if document already exists (except for custom)
                if doc_type != 'custom':
                    existing = get_document_by_project_and_type(project.id, doc_type)
                    if existing:
                        st.warning('This document type already exists. It will be regenerated.')
                
                title = DOC_TITLES[doc_type]
                
                # Start background generation
                thread = threading.Thread(
                    target=generate_document_async,
                    args=(project.id, doc_type, title, project.project_md, project.github_url),
                    daemon=True
                )
                thread.start()
                
                st.success('✅ Document generation started')
                st.info('Generating in background... Refresh to see progress.')
                st.rerun()
    
    # Load documents
    documents = get_documents_by_project(project.id)
    
    if not documents:
        st.info('No documents yet. Generate one above.')
    else:
        # Display PROJECT.md first
        with st.expander('📋 PROJECT.md (Repository Analysis)', expanded=True):
            st.markdown(project.project_md)
        
        # Display other documents
        for doc in documents:
            with st.expander(f'📄 {doc.title}'):
                st.markdown(doc.content)
                st.caption(f'Generated: {doc.created_at[:10]}')

def render_videos_tab(project):
    """Render videos tab"""
    
    st.subheader('Video Briefings')
    st.caption('Generate automated video briefings from documentation')
    
    # Load documents
    documents = get_documents_by_project(project.id)
    
    if not documents:
        st.info('Generate documents first before creating videos.')
        return
    
    # Video generation section
    with st.expander('➕ Generate New Video'):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            doc_options = {doc.id: f"{doc.title}" for doc in documents}
            selected_doc_id = st.selectbox(
                'Select Document',
                options=list(doc_options.keys()),
                format_func=lambda x: doc_options[x]
            )
        
        with col2:
            if st.button('Generate Video', type='primary', use_container_width=True):
                # Get document
                document = next((d for d in documents if d.id == selected_doc_id), None)
                if not document:
                    st.error('Document not found')
                    return
                
                # Create video record
                video_id = str(uuid.uuid4())
                video = Video(
                    id=video_id,
                    document_id=selected_doc_id,
                    status='pending',
                    video_url=None,
                    transcript=None,
                    storyboard=None,
                    created_at=datetime.now().isoformat()
                )
                
                create_video(video)
                
                # Start background generation
                thread = threading.Thread(
                    target=generate_video_async_wrapper,
                    args=(video_id, selected_doc_id, document),
                    daemon=True
                )
                thread.start()
                
                st.success('✅ Video generation started')
                st.info('This will take 3-5 minutes. Refresh to see progress.')
                st.rerun()
    
    # Display videos grouped by document
    st.markdown('---')
    st.subheader('Generated Videos')
    
    for document in documents:
        videos = get_videos_by_document(document.id)
        
        if videos:
            st.markdown(f'**{document.title}**')
            
            for video in videos:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    if video.status == 'ready' and video.video_url:
                        st.video(f'public{video.video_url}')
                    else:
                        status_icons = {
                            'pending': '🟡',
                            'generating': '🔵',
                            'ready': '🟢',
                            'error': '🔴'
                        }
                        icon = status_icons.get(video.status, '⚪')
                        st.info(f'{icon} Status: {video.status}')
                
                with col2:
                    st.caption(f'Created: {video.created_at[:10]}')
                
                with col3:
                    if video.status == 'error' and video.error_message:
                        st.error(f'Error: {video.error_message[:50]}...')
            
            st.markdown('---')
    
    # Auto-refresh for pending videos
    all_videos = []
    for doc in documents:
        all_videos.extend(get_videos_by_document(doc.id))
    
    if any(v.status in ['pending', 'generating'] for v in all_videos):
        st.info('🔄 Videos are being generated... (Auto-refreshing every 10 seconds)')
        import time
        time.sleep(10)
        st.rerun()

def render_chat_tab(project):
    """Render chat tab"""
    
    st.subheader('Chat with the Codebase')
    st.caption('Ask questions about the repository and get AI-powered answers')
    
    # Initialize chat history in session state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    if 'chat_session_id' not in st.session_state:
        st.session_state.chat_session_id = None
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
    
    # Chat input
    if prompt := st.chat_input('Ask a question about the codebase...'):
        # Add user message
        st.session_state.chat_messages.append({
            'role': 'user',
            'content': prompt
        })
        
        # Display user message
        with st.chat_message('user'):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message('assistant'):
            with st.spinner('Thinking...'):
                try:
                    # Get or create session
                    session = get_or_create_session(
                        project.id,
                        project.github_url,
                        st.session_state.chat_session_id
                    )
                    st.session_state.chat_session_id = session.session_id
                    
                    # Validate session repo path
                    if not os.path.exists(session.repo_path):
                        st.error(f'❌ Repository path no longer exists. Please refresh and try again.')
                        raise ValueError(f'Session repo path does not exist: {session.repo_path}')
                    
                    log.info(f'Chat using repository at: {session.repo_path}')
                    
                    # Create agent
                    repo_tools = create_repo_tools(session.repo_path)
                    qa_agent = QAAgent(repo_tools, project.project_md)
                    
                    # Get response
                    response = qa_agent.chat(st.session_state.chat_messages)
                    
                    # Add assistant message
                    st.session_state.chat_messages.append({
                        'role': 'assistant',
                        'content': response
                    })
                    
                    st.markdown(response)
                    
                except Exception as e:
                    error_msg = f'Error: {str(e)}'
                    st.error(error_msg)
                    st.session_state.chat_messages.append({
                        'role': 'assistant',
                        'content': error_msg
                    })
