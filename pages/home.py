"""
Home page - Repository submission and project list
"""

import streamlit as st
import uuid
from datetime import datetime
import threading

from lib.database import create_project, get_all_projects, update_project, update_project_status
from lib.types import Project
from lib.git import clone_repository, parse_github_url, get_or_create_session
from lib.tools import create_repo_tools
from lib.agents import MapperAgent
from lib.logger import create_logger

log = create_logger('HOME')

def process_repository_async(project_id: str, github_url: str):
    """Process repository in background"""
    try:
        log.info('=' * 80)
        log.info(f'REPOSITORY ANALYSIS START')
        log.info(f'Project ID: {project_id}')
        log.info(f'GitHub URL: {github_url}')
        log.info('=' * 80)
        
        # Use session manager to clone repository
        # This ensures the repo will be available for later operations
        session = get_or_create_session(project_id, github_url)
        repo_path = session.repo_path
        
        log.info(f'✅ Repository available at: {repo_path}')
        
        # Get commit SHA from the cloned repo
        try:
            from git import Repo
            repo = Repo(repo_path)
            commit_sha = repo.head.commit.hexsha
            update_project(project_id, {'commit_sha': commit_sha})
            log.info(f'Commit SHA: {commit_sha}')
        except Exception as e:
            log.warning(f'Could not get commit SHA: {e}')
        
        # Create tools and agent
        repo_tools = create_repo_tools(repo_path)
        log.info(f'✅ Created repo tools for path: {repo_path}')
        
        mapper_agent = MapperAgent(repo_tools)
        
        # Generate PROJECT.md
        log.info(f'🔄 Generating PROJECT.md for repository at: {repo_path}')
        update_project_status(project_id, 'generating')
        
        project_md = mapper_agent.analyze_repository()
        
        # Update project
        update_project(project_id, {
            'project_md': project_md,
            'status': 'ready'
        })
        
        log.info(f'✅ Project ready: {project_id}')
        log.info(f'📁 Repository kept at: {repo_path} (managed by session system)')
        log.info('=' * 80)
        
    except Exception as e:
        log.error(f'❌ Repository processing failed: {e}')
        log.error('=' * 80)
        update_project_status(project_id, 'error', str(e))

def render(navigate_to):
    """Render home page with clean UI"""
    
    # Hero Section
    st.markdown("""
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; 
                padding: 40px; margin-bottom: 32px; text-align: center;">
        <h1 style="color: #0f172a; font-size: 42px; margin: 0 0 8px 0;">📋 AI-Onboarder</h1>
        <p style="color: #64748b; font-size: 16px; margin: 0 0 16px 0;"><strong>by Hello World Programmers</strong></p>
        <p style="font-size: 18px; color: #64748b; margin: 0;">
            Transform GitHub repositories into comprehensive onboarding documentation
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features Section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: white; border: 1px solid #cbd5e1; border-radius: 12px; 
                    padding: 28px; text-align: center; height: 220px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 48px; margin-bottom: 16px;">📚</div>
            <h3 style="color: #0f172a; margin: 0 0 12px 0; font-size: 20px; font-weight: 600;">Documentation</h3>
            <p style="color: #64748b; margin: 0; font-size: 14px; line-height: 1.6;">Generate comprehensive documentation from your codebase automatically</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: white; border: 1px solid #cbd5e1; border-radius: 12px; 
                    padding: 28px; text-align: center; height: 220px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 48px; margin-bottom: 16px;">🎬</div>
            <h3 style="color: #0f172a; margin: 0 0 12px 0; font-size: 20px; font-weight: 600;">Video Briefings</h3>
            <p style="color: #64748b; margin: 0; font-size: 14px; line-height: 1.6;">Create engaging video explanations with AI-powered narration</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: white; border: 1px solid #cbd5e1; border-radius: 12px; 
                    padding: 28px; text-align: center; height: 220px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 48px; margin-bottom: 16px;">💬</div>
            <h3 style="color: #0f172a; margin: 0 0 12px 0; font-size: 20px; font-weight: 600;">Interactive Chat</h3>
            <p style="color: #64748b; margin: 0; font-size: 14px; line-height: 1.6;">Ask questions about your code and get instant answers</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Repository input section
    st.markdown("### 🚀 Add New Repository")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        github_url = st.text_input(
            'GitHub URL',
            placeholder='https://github.com/owner/repo',
            label_visibility='collapsed',
            help='Enter the full GitHub repository URL'
        )
    
    with col2:
        submit_button = st.button('Analyze', type='primary', use_container_width=True)
    
    # Handle submission
    if submit_button:
        if not github_url:
            st.error('Please enter a GitHub URL')
        else:
            # Validate URL
            repo_info = parse_github_url(github_url)
            if not repo_info:
                st.error('Invalid GitHub URL')
            else:
                # Create project
                project_id = str(uuid.uuid4())
                project = Project(
                    id=project_id,
                    github_url=github_url,
                    commit_sha='',
                    status='scanning',
                    project_md=None,
                    created_at=datetime.now().isoformat(),
                    repo_name=f'{repo_info.owner}/{repo_info.repo}'
                )
                
                create_project(project)
                
                # Start background processing
                thread = threading.Thread(
                    target=process_repository_async,
                    args=(project_id, github_url),
                    daemon=True
                )
                thread.start()
                
                st.success(f'✅ Repository submitted: {project.repo_name}')
                st.info('Processing in background... Refresh to see progress.')
                st.rerun()
    
    # Projects list
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📂 Your Projects")
    
    projects = get_all_projects()
    
    if not projects:
        st.markdown("""
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; 
                    padding: 40px; text-align: center; margin-top: 20px;">
            <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;">📭</div>
            <h3 style="color: #64748b; margin: 0; font-weight: 500;">No projects yet</h3>
            <p style="color: #94a3b8; margin: 8px 0 0 0;">Enter a GitHub URL above to get started</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display projects in a grid
        for i in range(0, len(projects), 2):
            cols = st.columns(2)
            
            for j, col in enumerate(cols):
                if i + j < len(projects):
                    with col:
                        render_project_card(projects[i + j], navigate_to)
    
    # Auto-refresh for pending projects (silent refresh - no message)
    if any(p.status in ['pending', 'scanning', 'generating'] for p in projects):
        import time
        time.sleep(5)
        st.rerun()

def render_project_card(project: Project, navigate_to):
    """Render a clean project card"""
    
    # Status styling
    status_config = {
        'pending': {'icon': '⏳', 'color': '#f59e0b', 'bg': '#fef3c7', 'text': 'Pending'},
        'scanning': {'icon': '🔍', 'color': '#3b82f6', 'bg': '#dbeafe', 'text': 'Scanning'},
        'generating': {'icon': '⚡', 'color': '#8b5cf6', 'bg': '#e9d5ff', 'text': 'Generating'},
        'ready': {'icon': '✅', 'color': '#10b981', 'bg': '#d1fae5', 'text': 'Ready'},
        'error': {'icon': '❌', 'color': '#ef4444', 'bg': '#fee2e2', 'text': 'Error'}
    }
    
    status = status_config.get(project.status, status_config['pending'])
    
    with st.container():
        st.markdown(f"""
        <div style="background: white; border: 1px solid #cbd5e1; border-radius: 12px; 
                    padding: 20px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                <h3 style="color: #0f172a; margin: 0; font-size: 16px; font-weight: 600;">
                    📦 {project.repo_name}
                </h3>
                <div style="background: {status['bg']}; padding: 4px 12px; border-radius: 6px;
                           font-weight: 500; font-size: 12px; color: {status['color']}; white-space: nowrap;">
                    {status['icon']} {status['text']}
                </div>
            </div>
            <p style="color: #64748b; margin: 0; font-size: 13px;">
                📅 {project.created_at[:10]}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if project.status == 'ready':
            if st.button(f'View Project', key=f'view_{project.id}', use_container_width=True):
                navigate_to('project', project.id)
        elif project.status == 'error':
            st.error(f'Error: {project.error_message or "Unknown error"}')
        else:
            st.info(f'Processing... {project.status}')
