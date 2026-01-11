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
    """Render home page"""
    
    st.title('🧠 AI-Onboarder')
    st.markdown('### Transform GitHub repositories into comprehensive onboarding documentation')
    
    # Repository input section
    st.markdown('---')
    st.subheader('Add Repository')
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        github_url = st.text_input(
            'GitHub URL',
            placeholder='https://github.com/owner/repo',
            label_visibility='collapsed'
        )
    
    with col2:
        submit_button = st.button('Analyze Repository', type='primary', use_container_width=True)
    
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
    st.markdown('---')
    st.subheader('Your Projects')
    
    projects = get_all_projects()
    
    if not projects:
        st.info('No projects yet. Enter a GitHub URL above to get started.')
    else:
        # Display projects in a grid
        for i in range(0, len(projects), 2):
            cols = st.columns(2)
            
            for j, col in enumerate(cols):
                if i + j < len(projects):
                    with col:
                        render_project_card(projects[i + j], navigate_to)
    
    # Auto-refresh for pending projects
    if any(p.status in ['pending', 'scanning', 'generating'] for p in projects):
        st.info('🔄 Projects are being processed... (Auto-refreshing every 5 seconds)')
        import time
        time.sleep(5)
        st.rerun()

def render_project_card(project: Project, navigate_to):
    """Render a project card"""
    
    # Status badge
    status_colors = {
        'pending': '🟡',
        'scanning': '🔵',
        'generating': '🟣',
        'ready': '🟢',
        'error': '🔴'
    }
    status_icon = status_colors.get(project.status, '⚪')
    
    with st.container():
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <h4>{project.repo_name}</h4>
            <p><strong>Status:</strong> {status_icon} {project.status.upper()}</p>
            <p><strong>Created:</strong> {project.created_at[:10]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if project.status == 'ready':
            if st.button(f'View Project', key=f'view_{project.id}', use_container_width=True):
                navigate_to('project', project.id)
        elif project.status == 'error':
            st.error(f'Error: {project.error_message or "Unknown error"}')
        else:
            st.info(f'Processing... {project.status}')
