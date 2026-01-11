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
    update_video_status, update_document_status, delete_document_by_type
)
from lib.types import Document, Video
from lib.git import get_or_create_session, get_existing_session
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
    'user_flows': 'User Journeys',
    'troubleshooting': 'Troubleshooting Guide',
    'custom': 'Custom Document'
}

def generate_document_async(document_id: str, project_id: str, doc_type: str, title: str, project_md: str, github_url: str):
    """Generate document in background"""
    try:
        log.info('=' * 80)
        log.info(f'DOCUMENT GENERATION START')
        log.info(f'Document ID: {document_id}')
        log.info(f'Project ID: {project_id}')
        log.info(f'Doc Type: {doc_type}')
        log.info(f'GitHub URL: {github_url}')
        log.info('=' * 80)
        
        # Update status to generating
        update_document_status(document_id, 'generating')
        
        # Try to get existing session (reuse cloned repo from session system)
        context_only_mode = False
        repo_path = None
        
        try:
            # Check session system first
            session = get_existing_session(project_id, github_url)
            
            if session and os.path.exists(session.repo_path):
                log.info(f'✅ Using repository from active session: {session.repo_path}')
                repo_path = session.repo_path
            else:
                log.info('📋 No active session found - using PROJECT.md context-only mode')
                context_only_mode = True
        except Exception as e:
            log.warning(f'⚠️ Could not access repository: {e}')
            log.info('📋 Falling back to PROJECT.md context-only mode')
            context_only_mode = True
        
        # Generate document based on available resources
        if context_only_mode:
            # Generate from PROJECT.md only (no repo access)
            log.info('🔄 Generating from PROJECT.md context only')
            from lib.agents.doc_agents import DocAgent
            agent = DocAgent(doc_type, None)  # No repo tools
            content = agent.generate_doc(project_md, title, context_only=True)
        else:
            # Full mode with repo exploration
            log.info(f'🔄 Generating with full repository access: {repo_path}')
            repo_tools = create_repo_tools(repo_path)
            doc_agents = create_doc_agents(repo_tools)
            
            agent = doc_agents.get(doc_type)
            if not agent:
                raise ValueError(f'Unknown document type: {doc_type}')
            
            content = agent.generate_doc(project_md, title, context_only=False)
        
        # Update document with content and mark as ready
        update_document_status(document_id, 'ready', content=content)
        log.info(f'✅ Document ready: {document_id}')
        
    except Exception as e:
        log.error(f'❌ Document generation failed: {e}')
        import traceback
        traceback.print_exc()
        update_document_status(document_id, 'error', error_message=str(e))

def generate_video_async_wrapper(video_id: str, document_id: str, document: Document, color_scheme: str = 'ocean'):
    """Generate video in background"""
    try:
        log.info(f'Generating video for document: {document_id} with theme: {color_scheme}')
        
        # Generate storyboard
        update_video_status(video_id, 'generating')
        storyboard = generate_storyboard(document.title, document.content)
        
        # Generate video with asyncio
        async def gen():
            result = await generate_video_async(video_id, storyboard, color_scheme=color_scheme)
            
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
    
    # Auto-generate Platform Overview on first view (if not exists)
    overview_doc = get_document_by_project_and_type(project.id, 'overview')
    if not overview_doc:
        st.info('🚀 **First Time Setup**: Auto-generating Platform Overview...')
        
        # Create pending overview document
        document_id = str(uuid.uuid4())
        overview = Document(
            id=document_id,
            project_id=project.id,
            type='overview',
            title='Platform Overview',
            content='',
            diagram_url=None,
            created_at=datetime.now().isoformat(),
            status='pending',
            error_message=None
        )
        create_document(overview)
        
        # Start background generation
        thread = threading.Thread(
            target=generate_document_async,
            args=(document_id, project.id, 'overview', 'Platform Overview', project.project_md, project.github_url),
            daemon=True
        )
        thread.start()
        
        st.success('✅ Platform Overview generation started!')
        import time
        time.sleep(2)
        st.rerun()
    
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
    
    # Get existing documents
    docs = get_documents_by_project(project.id)
    
    # Auto-generate overview if no documents exist
    if not docs:
        st.info('🔄 No documents found. Auto-generating Platform Overview...')
        
        # Auto-generate overview document
        doc_id = str(uuid.uuid4())
        title = 'Platform Overview'
        doc_type = 'overview'
        
        create_document(doc_id, project.id, doc_type, title, status='generating')
        
        # Start background generation
        thread = threading.Thread(
            target=generate_document_async,
            args=(doc_id, project.id, doc_type, title, project.project_md, project.github_url)
        )
        thread.daemon = True
        thread.start()
        
        time.sleep(0.5)  # Brief pause for generation to start
        st.rerun()
        return
    
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
                        if existing.status == 'generating':
                            st.warning('⏳ This document is already being generated...')
                            st.stop()
                        elif existing.status == 'ready':
                            st.info('ℹ️ This document type already exists. It will be regenerated.')
                            # Delete existing document before regenerating
                            delete_document_by_type(project.id, doc_type)
                
                title = DOC_TITLES[doc_type]
                
                # Create pending document first
                document_id = str(uuid.uuid4())
                document = Document(
                    id=document_id,
                    project_id=project.id,
                    type=doc_type,
                    title=title,
                    content='',
                    diagram_url=None,
                    created_at=datetime.now().isoformat(),
                    status='pending',
                    error_message=None
                )
                create_document(document)
                
                # Start background generation
                thread = threading.Thread(
                    target=generate_document_async,
                    args=(document_id, project.id, doc_type, title, project.project_md, project.github_url),
                    daemon=True
                )
                thread.start()
                
                st.success('✅ Document generation started!')
                st.info('🔄 Generating... The page will auto-refresh to show progress.')
                st.rerun()
    
    # Check if repository is available via session system
    session = get_existing_session(project.id, project.github_url)
    repo_available = session is not None and os.path.exists(session.repo_path) if session else False
    
    if not repo_available:
        st.markdown("""
        <div style="background: #fef3c7; border: 1px solid #fbbf24; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;">
            <span style="color: #92400e; font-size: 14px;">⚠️ <strong>Repository Unavailable</strong>: Documents will be generated from PROJECT.md context only</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: #dcfce7; border: 1px solid #86efac; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;">
            <span style="color: #166534; font-size: 14px;">✅ <strong>Repository Available</strong>: Documents will be generated with full code exploration</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Load documents
    documents = get_documents_by_project(project.id)
    
    # Check if any documents are generating (for auto-refresh)
    has_generating = any(doc.status == 'generating' or doc.status == 'pending' for doc in documents)
    if has_generating:
        st.info('⏳ Documents are being generated... This page will auto-refresh.')
        import time
        time.sleep(3)
        st.rerun()
    
    if not documents:
        st.info('No documents yet. Generate one above.')
    else:
        # Display PROJECT.md first
        with st.expander('📋 PROJECT.md (Repository Analysis)', expanded=True):
            st.markdown(project.project_md)
        
        # Display other documents
        for doc in documents:
            # Status indicator
            status_emoji = {
                'pending': '⏳',
                'generating': '🔄',
                'ready': '✅',
                'error': '❌'
            }
            emoji = status_emoji.get(doc.status, '❓')
            
            with st.expander(f'{emoji} {doc.title} ({doc.status.upper()})'):
                if doc.status == 'ready':
                    st.markdown(doc.content)
                    st.caption(f'Generated: {doc.created_at[:10]}')
                elif doc.status == 'generating':
                    st.info('🔄 Generating document... Please wait.')
                    st.spinner('Processing...')
                elif doc.status == 'pending':
                    st.info('⏳ Waiting to start generation...')
                elif doc.status == 'error':
                    st.error(f'❌ Generation failed: {doc.error_message}')
                    st.caption(f'Created: {doc.created_at[:10]}')

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
    with st.expander('➕ Generate New Video', expanded=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            doc_options = {doc.id: f"{doc.title}" for doc in documents}
            selected_doc_id = st.selectbox(
                'Select Document',
                options=list(doc_options.keys()),
                format_func=lambda x: doc_options[x]
            )
        
        with col2:
            color_scheme = st.selectbox(
                'Visual Theme',
                options=['ocean', 'minimal', 'midnight'],
                format_func=lambda x: {
                    'ocean': '🌊 Ocean Blue',
                    'minimal': '✨ Clean & Minimal',
                    'midnight': '🌙 Midnight Purple'
                }[x]
            )
        
        with col3:
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
                    args=(video_id, selected_doc_id, document, color_scheme),
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
    """Render ChatGPT-style chat interface"""
    
    # Initialize chat history in session state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    if 'chat_session_id' not in st.session_state:
        st.session_state.chat_session_id = None
    
    # Initialize or refresh context mode flag based on current session status
    session = get_existing_session(project.id, project.github_url)
    st.session_state.chat_context_mode = session is None
    
    # Clear chat button in corner
    if len(st.session_state.chat_messages) > 0:
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("🗑️ Clear", use_container_width=True, key="clear_chat_btn"):
                st.session_state.chat_messages = []
                st.rerun()
    
    # Welcome message if chat is empty
    if len(st.session_state.chat_messages) == 0:
        st.markdown("""
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; 
                    padding: 32px; margin-bottom: 24px; text-align: center;">
            <h2 style="color: #0f172a; margin: 0 0 12px 0; font-size: 24px;">💬 Chat with Your Codebase</h2>
            <p style="font-size: 15px; color: #64748b; margin: 0;">
                Ask me anything about this repository. I can explain code, architecture, and functionality.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Example questions
        st.markdown("**💡 Example questions:**")
        
        col1, col2 = st.columns(2)
        
        example_questions = [
            "What is this project about?",
            "Explain the main architecture",
            "How does authentication work?",
            "What are the key features?",
            "Show me the database schema",
            "How do I run this locally?"
        ]
        
        for i, question in enumerate(example_questions):
            col = col1 if i % 2 == 0 else col2
            with col:
                # Use a unique key and handle click properly
                if st.button(question, key=f"example_q_{i}", use_container_width=True, type="secondary"):
                    # Add user message immediately
                    st.session_state.chat_messages.append({
                        'role': 'user',
                        'content': question
                    })
                    # Add thinking indicator
                    st.session_state.chat_messages.append({
                        'role': 'assistant',
                        'content': '__THINKING__'
                    })
                    # Store for processing in next render
                    st.session_state.pending_message = question
                    st.rerun()
        
        st.markdown("---")
    
    # Chat messages container with auto-scroll
    chat_container = st.container()
    
    with chat_container:
        # Display all messages
        for idx, message in enumerate(st.session_state.chat_messages):
            if message['role'] == 'user':
                # User message on the RIGHT
                col1, col2 = st.columns([3, 7])
                with col2:
                    st.markdown(f"""
                    <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; 
                                padding: 12px 16px; margin: 8px 0; border-left: 3px solid #ef4444;">
                        <div style="color: #991b1b; font-weight: 600; font-size: 13px; margin-bottom: 4px;">👤 You</div>
                        <div style="color: #1e293b;">{message['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Assistant message on the LEFT
                col1, col2 = st.columns([7, 3])
                with col1:
                    # Check if this is a thinking indicator
                    if message['content'] == '__THINKING__':
                        st.markdown("""
                        <div style="background: #eff6ff; border: 1px solid #dbeafe; border-radius: 12px; 
                                    padding: 12px 16px; margin: 8px 0; border-left: 3px solid #3b82f6;">
                            <div style="color: #1e40af; font-weight: 600; font-size: 13px; margin-bottom: 4px;">🤖 AI Assistant</div>
                            <div style="color: #64748b; line-height: 1.6;">💭 Thinking and analyzing your question...</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: #eff6ff; border: 1px solid #dbeafe; border-radius: 12px; 
                                    padding: 12px 16px; margin: 8px 0; border-left: 3px solid #3b82f6;">
                            <div style="color: #1e40af; font-weight: 600; font-size: 13px; margin-bottom: 4px;">🤖 AI Assistant</div>
                            <div style="color: #1e293b; line-height: 1.6;">{message['content']}</div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Auto-scroll to bottom using JavaScript
    st.markdown("""
    <script>
        // Auto-scroll chat to bottom
        setTimeout(function() {
            var elements = window.parent.document.querySelectorAll('[data-testid="stVerticalBlock"]');
            if (elements.length > 0) {
                var chatContainer = elements[elements.length - 1];
                chatContainer.scrollTo({
                    top: chatContainer.scrollHeight,
                    behavior: 'smooth'
                });
            }
        }, 100);
    </script>
    """, unsafe_allow_html=True)
    
    # Check if we need to process a pending message
    if 'pending_message' in st.session_state:
        pending_msg = st.session_state.pending_message
        del st.session_state.pending_message
        process_chat_message(project, pending_msg)
        st.rerun()
    
    # Show context warning if in fallback mode
    if st.session_state.get('chat_context_mode', False):
        st.markdown("""
        <div style="background: #fef3c7; border: 1px solid #fbbf24; border-radius: 8px; 
                    padding: 10px 16px; margin-bottom: 12px;">
            <span style="color: #92400e; font-weight: 500; font-size: 13px;">
                ⚠️ Context Mode: Using PROJECT.md summary (repository session unavailable)
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    # Chat input at bottom
    prompt = st.chat_input('💭 Ask a question about the codebase...', key='chat_input')
    
    if prompt:
        # Add user message immediately
        st.session_state.chat_messages.append({
            'role': 'user',
            'content': prompt
        })
        
        # Add thinking indicator
        st.session_state.chat_messages.append({
            'role': 'assistant',
            'content': '__THINKING__'
        })
        
        # Store message for processing in next render
        st.session_state.pending_message = prompt
        st.rerun()

def process_chat_message(project, user_message):
    """Process chat message and get AI response"""
    try:
        # Remove thinking indicator if present
        if st.session_state.chat_messages and st.session_state.chat_messages[-1].get('content') == '__THINKING__':
            st.session_state.chat_messages.pop()
        
        # Check for existing session WITHOUT creating new one
        context_only = False
        repo_path = None
        
        session = get_existing_session(project.id, project.github_url)
        
        if session and os.path.exists(session.repo_path):
            # Valid session exists
            st.session_state.chat_session_id = session.session_id
            st.session_state.chat_context_mode = False  # Update flag - we have repo
            repo_path = session.repo_path
            log.info(f'Chat using repository at: {repo_path}')
        else:
            # No valid session - use PROJECT.md fallback
            context_only = True
            st.session_state.chat_context_mode = True  # Update flag - using fallback
            log.info(f'No valid session found. Chat using PROJECT.md context only')
        
        # Create agent with appropriate mode
        if context_only:
            repo_tools = None  # No tools needed for context-only mode
        else:
            repo_tools = create_repo_tools(repo_path)
        
        qa_agent = QAAgent(repo_tools, project.project_md, context_only=context_only)
        
        # Get response
        response = qa_agent.chat(st.session_state.chat_messages)
        
        # Add assistant message (replaces thinking indicator)
        st.session_state.chat_messages.append({
            'role': 'assistant',
            'content': response
        })
        
    except Exception as e:
        # Remove thinking indicator if present
        if st.session_state.chat_messages and st.session_state.chat_messages[-1].get('content') == '__THINKING__':
            st.session_state.chat_messages.pop()
        
        error_msg = f'Error: {str(e)}'
        log.error(error_msg)
        st.session_state.chat_messages.append({
            'role': 'assistant',
            'content': f'❌ {error_msg}'
        })
