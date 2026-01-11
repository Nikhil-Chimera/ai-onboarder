"""
Repository exploration tools for AI agents
"""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from lib.types import TreeEntry, GrepHit

# Default ignore patterns
IGNORE_PATTERNS = [
    'node_modules',
    '.git',
    'dist',
    'build',
    'coverage',
    '.next',
    '__pycache__',
    'vendor',
    '.cache',
    '*.lock',
    '*.min.js',
    '*.map',
    '*.png',
    '*.jpg',
    '*.gif',
    '*.ico',
    '*.woff',
    '*.woff2',
    '*.ttf',
    '*.eot',
    '*.svg',
    '*.mp4',
    '*.mp3',
    '*.pdf',
    '*.zip',
    '*.tar',
    '*.gz',
]

def should_ignore(file_path: str) -> bool:
    """Check if a file should be ignored"""
    name = os.path.basename(file_path)
    
    for pattern in IGNORE_PATTERNS:
        if pattern.startswith('*.'):
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern or f'/{pattern}/' in file_path:
            return True
    
    return False

class RepoTools:
    """Tools for exploring a repository"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        
        # Validate repository path exists
        if not os.path.exists(repo_path):
            raise ValueError(f'Repository path does not exist: {repo_path}')
        
        # Log repository info for debugging
        try:
            # Try to detect .git directory or key files
            if os.path.exists(os.path.join(repo_path, '.git')):
                # This is a git repo
                pass
            # Count files to ensure it's not empty
            file_count = sum(1 for _ in Path(repo_path).rglob('*') if _.is_file())
            if file_count == 0:
                raise ValueError(f'Repository path is empty: {repo_path}')
        except Exception as e:
            # Non-critical, just log warning
            import logging
            logging.warning(f'Could not validate repo structure: {e}')
    
    def list_tree(self, path: str = '.') -> Dict[str, Any]:
        """
        List contents of a directory (one level only)
        
        Args:
            path: Relative path from repo root
            
        Returns:
            Dict with listing, directories, files, and total count
        """
        full_path = os.path.join(self.repo_path, path)
        entries: List[TreeEntry] = []
        
        if not os.path.exists(full_path):
            return {
                'error': f'Directory not found: {path}',
                'listing': '',
                'directories': [],
                'files': [],
                'total': 0
            }
        
        try:
            items = os.listdir(full_path)
            
            for item in items:
                item_path = os.path.join(full_path, item)
                rel_path = os.path.relpath(item_path, self.repo_path)
                
                if should_ignore(rel_path):
                    continue
                
                if os.path.isdir(item_path):
                    # Count children
                    try:
                        children = [c for c in os.listdir(item_path) if not should_ignore(c)]
                        child_count = len(children)
                    except:
                        child_count = 0
                    
                    entries.append(TreeEntry(
                        path=rel_path.replace('\\', '/'),
                        type='directory',
                        size=child_count
                    ))
                elif os.path.isfile(item_path):
                    try:
                        size = os.path.getsize(item_path)
                        entries.append(TreeEntry(
                            path=rel_path.replace('\\', '/'),
                            type='file',
                            size=size
                        ))
                    except:
                        pass
            
            # Sort: directories first, then files
            entries.sort(key=lambda e: (e.type != 'directory', e.path))
            
            # Format listing
            listing_lines = []
            for entry in entries:
                name = os.path.basename(entry.path)
                if entry.type == 'directory':
                    listing_lines.append(f'📁 {name}/ ({entry.size} items)')
                else:
                    size_kb = entry.size // 1024 if entry.size > 1024 else entry.size
                    unit = 'KB' if entry.size > 1024 else 'B'
                    listing_lines.append(f'📄 {name} ({size_kb}{unit})')
            
            return {
                'path': path,
                'listing': '\n'.join(listing_lines),
                'directories': [e.path for e in entries if e.type == 'directory'],
                'files': [e.path for e in entries if e.type == 'file'],
                'total': len(entries)
            }
            
        except Exception as e:
            return {
                'error': f'Failed to list directory: {str(e)}',
                'listing': '',
                'directories': [],
                'files': [],
                'total': 0
            }
    
    def read_file(self, path: str, offset: int = 0, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Read contents of a file
        
        Args:
            path: Relative path from repo root
            offset: Starting line number (0-indexed)
            limit: Maximum number of lines to read (None = unlimited)
            
        Returns:
            Dict with content, total lines, and range info
        """
        full_path = os.path.join(self.repo_path, path)
        
        if not os.path.exists(full_path):
            return {
                'error': f'File not found: {path}',
                'content': '',
                'totalLines': 0,
                'startLine': 0,
                'endLine': 0,
                'truncated': False
            }
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            effective_limit = limit if limit is not None else total_lines
            
            selected_lines = lines[offset:offset + effective_limit]
            truncated = offset + effective_limit < total_lines
            
            # Add line numbers
            numbered_lines = [
                f'{offset + i + 1}: {line.rstrip()}'
                for i, line in enumerate(selected_lines)
            ]
            
            return {
                'content': '\n'.join(numbered_lines),
                'totalLines': total_lines,
                'startLine': offset + 1,
                'endLine': min(offset + effective_limit, total_lines),
                'truncated': truncated
            }
            
        except Exception as e:
            return {
                'error': f'Failed to read file: {str(e)}',
                'content': '',
                'totalLines': 0,
                'startLine': 0,
                'endLine': 0,
                'truncated': False
            }
    
    def grep(self, pattern: str, file_pattern: Optional[str] = None, max_results: int = 1000) -> Dict[str, Any]:
        """
        Search for a pattern in files
        
        Args:
            pattern: Search pattern (case-insensitive)
            file_pattern: Optional glob pattern to filter files
            max_results: Maximum number of results
            
        Returns:
            Dict with hits and total count
        """
        hits: List[GrepHit] = []
        pattern_lower = pattern.lower()
        
        try:
            for root, dirs, files in os.walk(self.repo_path):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.repo_path).replace('\\', '/')
                    
                    if should_ignore(rel_path):
                        continue
                    
                    # Apply file pattern filter
                    if file_pattern and not self._match_pattern(rel_path, file_pattern):
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_no, line in enumerate(f, 1):
                                if pattern_lower in line.lower():
                                    hits.append(GrepHit(
                                        path=rel_path,
                                        line_no=line_no,
                                        excerpt=line.strip()[:200]  # Limit excerpt length
                                    ))
                                    
                                    if len(hits) >= max_results:
                                        break
                    except:
                        continue
                    
                    if len(hits) >= max_results:
                        break
                
                if len(hits) >= max_results:
                    break
            
            # Format results
            result_lines = []
            for hit in hits[:100]:  # Show first 100 in summary
                result_lines.append(f'{hit.path}:{hit.line_no} - {hit.excerpt}')
            
            return {
                'pattern': pattern,
                'hits': result_lines,
                'total': len(hits),
                'truncated': len(hits) >= max_results
            }
            
        except Exception as e:
            return {
                'error': f'Search failed: {str(e)}',
                'hits': [],
                'total': 0,
                'truncated': False
            }
    
    def read_snippet(self, path: str, start_line: int, end_line: int, context_lines: int = 10) -> Dict[str, Any]:
        """
        Read a specific section of a file with context
        
        Args:
            path: Relative path from repo root
            start_line: Starting line (1-indexed)
            end_line: Ending line (1-indexed)
            context_lines: Number of context lines before/after
            
        Returns:
            Dict with content and actual range
        """
        full_path = os.path.join(self.repo_path, path)
        
        if not os.path.exists(full_path):
            return {
                'error': f'File not found: {path}',
                'content': '',
                'actualRange': {'start': 0, 'end': 0}
            }
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # Add context
            actual_start = max(1, start_line - context_lines)
            actual_end = min(total_lines, end_line + context_lines)
            
            selected_lines = lines[actual_start - 1:actual_end]
            
            # Add line numbers
            numbered_lines = [
                f'{actual_start + i}: {line.rstrip()}'
                for i, line in enumerate(selected_lines)
            ]
            
            return {
                'content': '\n'.join(numbered_lines),
                'actualRange': {
                    'start': actual_start,
                    'end': actual_end
                }
            }
            
        except Exception as e:
            return {
                'error': f'Failed to read snippet: {str(e)}',
                'content': '',
                'actualRange': {'start': 0, 'end': 0}
            }
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Simple glob pattern matching"""
        # Convert glob to regex
        regex_pattern = pattern.replace('.', r'\.').replace('*', '.*').replace('?', '.')
        return bool(re.match(regex_pattern, path))

def create_repo_tools(repo_path: str) -> RepoTools:
    """Factory function to create repo tools with validation"""
    import logging
    log = logging.getLogger('TOOLS')
    
    log.info(f'Creating RepoTools for: {repo_path}')
    
    # Validate path exists
    if not os.path.exists(repo_path):
        raise ValueError(f'❌ Repository path does not exist: {repo_path}')
    
    # List some files to verify it's the right repo
    try:
        files = os.listdir(repo_path)[:10]
        log.info(f'Repository contains: {files}')
    except Exception as e:
        log.warning(f'Could not list repo contents: {e}')
    
    return RepoTools(repo_path)
