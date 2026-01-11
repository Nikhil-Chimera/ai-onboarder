"""
Git operations for cloning and managing repositories
"""

import os
import tempfile
import re
import shutil
from typing import Optional, Tuple
from git import Repo, GitCommandError
import requests

from lib.types import RepoInfo
from lib.logger import create_logger

log = create_logger('GIT')

def parse_github_url(url: str) -> Optional[RepoInfo]:
    """Parse a GitHub URL to extract owner, repo, and branch"""
    log.info(f'Parsing GitHub URL: {url}')
    
    # Support various GitHub URL formats
    patterns = [
        r'^(?:https?://)?github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/tree/([^/]+))?$',
        r'^(?:https?://)?github\.com/([^/]+)/([^/]+?)(?:\.git)?$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, url.strip())
        if match:
            owner = match.group(1)
            repo = match.group(2).replace('.git', '')
            branch = match.group(3) if len(match.groups()) >= 3 and match.group(3) else 'main'
            
            result = RepoInfo(
                owner=owner,
                repo=repo,
                branch=branch,
                commit_sha=''
            )
            log.info(f'URL parsed: {owner}/{repo} (branch: {branch})')
            return result
    
    log.error('Failed to parse GitHub URL')
    return None

def get_default_branch(owner: str, repo: str) -> str:
    """Fetch the default branch from GitHub API"""
    try:
        url = f'https://api.github.com/repos/{owner}/{repo}'
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AI-Onboarder-App'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.ok:
            data = response.json()
            default_branch = data.get('default_branch', 'main')
            log.info(f'Default branch from API: {default_branch}')
            return default_branch
        else:
            log.warning(f'GitHub API returned status {response.status_code}, using "main"')
            return 'main'
    except Exception as e:
        log.warning(f'Error fetching default branch: {e}, using "main"')
        return 'main'

def clone_repository(github_url: str) -> Tuple[str, RepoInfo]:
    """
    Clone a GitHub repository to a temporary directory
    
    Returns:
        Tuple of (repo_path, repo_info)
    """
    log.info('=' * 80)
    log.info(f'Starting clone operation for: {github_url}')
    
    repo_info = parse_github_url(github_url)
    if not repo_info:
        raise ValueError('Invalid GitHub URL')
    
    # Fetch actual default branch if using 'main'
    if repo_info.branch == 'main':
        repo_info.branch = get_default_branch(repo_info.owner, repo_info.repo)
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix='ai_onboarder_')
    repo_path = os.path.join(temp_dir, repo_info.repo)
    
    log.info(f'Temp directory: {temp_dir}')
    log.info(f'Cloning {repo_info.owner}/{repo_info.repo} (branch: {repo_info.branch})...')
    
    clone_url = f'https://github.com/{repo_info.owner}/{repo_info.repo}.git'
    
    try:
        # Clone with depth 1 for faster cloning
        repo = Repo.clone_from(
            clone_url,
            repo_path,
            branch=repo_info.branch,
            depth=1,
            single_branch=True
        )
        
        # Get commit SHA
        repo_info.commit_sha = repo.head.commit.hexsha
        
        log.info(f'Clone successful!')
        log.info(f'Commit SHA: {repo_info.commit_sha}')
        log.info(f'Repository path: {repo_path}')
        log.info('=' * 80)
        
        return repo_path, repo_info
        
    except GitCommandError as e:
        log.error(f'Git clone failed: {str(e)}')
        
        # Try with master branch as fallback
        if repo_info.branch == 'main':
            try:
                log.info('Retrying with "master" branch...')
                repo_info.branch = 'master'
                
                repo = Repo.clone_from(
                    clone_url,
                    repo_path,
                    branch='master',
                    depth=1,
                    single_branch=True
                )
                
                repo_info.commit_sha = repo.head.commit.hexsha
                log.info(f'Clone successful with master branch!')
                log.info(f'Commit SHA: {repo_info.commit_sha}')
                return repo_path, repo_info
                
            except GitCommandError as e2:
                log.error(f'Clone with master also failed: {str(e2)}')
                cleanup_repository(repo_path)
                raise ValueError(f'Failed to clone repository: {str(e2)}')
        
        cleanup_repository(repo_path)
        raise ValueError(f'Failed to clone repository: {str(e)}')
    
    except Exception as e:
        log.error(f'Unexpected error during clone: {str(e)}')
        cleanup_repository(repo_path)
        raise

def cleanup_repository(repo_path: str):
    """Clean up a cloned repository"""
    if os.path.exists(repo_path):
        try:
            # Get the parent temp directory
            parent_dir = os.path.dirname(repo_path)
            shutil.rmtree(parent_dir, ignore_errors=True)
            log.info(f'Cleaned up repository at {repo_path}')
        except Exception as e:
            log.warning(f'Failed to cleanup repository: {e}')
