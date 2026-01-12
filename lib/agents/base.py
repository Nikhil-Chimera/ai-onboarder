"""
Base agent class using Google Gemini AI
"""

import os
from typing import List, Dict, Any, Callable, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

from lib.logger import create_logger
from lib.tools.repo_tools import RepoTools

load_dotenv()

log = create_logger('AGENT')

# Configure Gemini with new SDK
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    log.warning('GOOGLE_API_KEY not found in environment')

# Use Gemini 2.0 Flash Experimental - latest stable model
# Fast, powerful, 1M context window
MODEL_NAME = 'gemini-2.5-pro'

class BaseAgent:
    """Base class for AI agents with tool support"""
    
    def __init__(self, system_prompt: str, repo_tools: Optional[RepoTools] = None):
        self.system_prompt = system_prompt
        self.repo_tools = repo_tools
        
        # Create a dedicated client per agent instance to avoid cross-contamination
        # This ensures each agent's conversations are isolated
        if not api_key:
            raise ValueError('Gemini client not initialized - check GOOGLE_API_KEY')
        self.client = genai.Client(api_key=api_key)
        
        # Define tools for Gemini
        self.tools = self._define_tools() if repo_tools else []
        
        # Generate a unique session ID for this agent instance
        import uuid
        self.session_id = str(uuid.uuid4())[:8]
        
        # Log repository info for debugging
        if repo_tools:
            log.info(f'[{self.session_id}] Agent initialized with repository: {repo_tools.repo_path}')
            log.info(f'[{self.session_id}] Tools available: {[t["function_declarations"][0]["name"] for t in self.tools] if self.tools else "none"}')
            import os
            if os.path.exists(repo_tools.repo_path):
                try:
                    files = os.listdir(repo_tools.repo_path)[:10]
                    log.info(f'Repository contains: {files}')
                except:
                    log.warning('Could not list repository contents')
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define tools in Gemini API format"""
        return [{
            "function_declarations": [
                {
                    "name": "listTree",
                    "description": "List the contents of a directory (one level only). Returns array of entries with path, type (file/directory), and size. Use this to explore the repository structure.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path from repository root (e.g., '.' for root, 'src' for src directory)"
                            }
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "readFile",
                    "description": "Read the contents of a file. Returns the file content as text. Use this to examine source code, configuration files, documentation, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to the file from repository root"
                            },
                            "offset": {
                                "type": "integer",
                                "description": "Starting byte offset (default: 0)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum bytes to read (default: 50000)"
                            }
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "grep",
                    "description": "Search for a pattern across the entire codebase. Returns matching lines with file paths and line numbers. Use this to find specific functions, classes, patterns, or keywords.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Search pattern (plain text or regex)"
                            },
                            "filePattern": {
                                "type": "string",
                                "description": "Optional glob pattern to limit search to specific files (e.g., '*.js', '*.py')"
                            },
                            "maxResults": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 1000)"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            ]
        }]
    
    def generate(self, prompt: str, max_iterations: int = 500) -> str:
        """
        Generate a response with tool support (UNLIMITED tool calls)
        
        Args:
            prompt: User prompt
            max_iterations: Maximum tool call iterations (default 500 for thorough exploration)
            
        Returns:
            Generated text response
        """
        session_id = getattr(self, 'session_id', 'unknown')
        log.info(f'[{session_id}] Generating response (max iterations: {max_iterations})')
        log.info(f'[{session_id}] Tools registered: {len(self.tools)} tool sets')
        if self.repo_tools:
            log.info(f'[{session_id}] Repository: {self.repo_tools.repo_path}')
        
        try:
            # Build config with tools
            config = types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                temperature=0.2,  # Lower temperature for more focused exploration
                max_output_tokens=8192,  # Ensure complete responses
                tools=self.tools if self.tools else None
            )
            
            # Start with user prompt
            messages = [
                types.Content(role='user', parts=[types.Part(text=prompt)])
            ]
            
            iteration = 0
            while iteration < max_iterations:
                # Generate response
                log.info(f'[{session_id}] Iteration {iteration + 1}/{max_iterations}')
                response = self.client.models.generate_content(
                    model=MODEL_NAME,
                    contents=messages,
                    config=config
                )
                
                # Check if response has text (final answer)
                if hasattr(response, 'text') and response.text:
                    log.info(f'[{session_id}] ✅ Response generated after {iteration} tool calls')
                    return response.text
                
                # Check for function calls
                has_function_call = False
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    
                    # Check if content is None (blocked by safety filters)
                    if not hasattr(candidate, 'content') or candidate.content is None:
                        log.error(f'[{session_id}] ❌ API response blocked (content is None) - likely safety filter or rate limit')
                        if hasattr(candidate, 'finish_reason'):
                            log.error(f'[{session_id}]    Finish reason: {candidate.finish_reason}')
                        if hasattr(candidate, 'safety_ratings'):
                            log.error(f'[{session_id}]    Safety ratings: {candidate.safety_ratings}')
                        raise ValueError('API response was blocked. This may be due to safety filters or rate limiting.')
                    
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call'):
                                has_function_call = True
                                func_call = part.function_call
                                tool_name = func_call.name
                                tool_args = dict(func_call.args) if hasattr(func_call, 'args') else {}
                                
                                log.info(f'[{session_id}] 🔧 Tool call [{iteration + 1}]: {tool_name}({tool_args})')
                                if self.repo_tools:
                                    log.info(f'[{session_id}]    Repository: {self.repo_tools.repo_path}')
                                
                                # Execute tool
                                if self.repo_tools:
                                    result = self._execute_tool(tool_name, tool_args)
                                    log.info(f'[{session_id}]    Result: {str(result)[:200]}...')
                                    
                                    # Add assistant's function call to history
                                    messages.append(candidate.content)
                                    
                                    # Add function response
                                    function_response_part = types.Part(
                                        function_response=types.FunctionResponse(
                                            name=tool_name,
                                            response={"result": result}
                                        )
                                    )
                                    messages.append(
                                        types.Content(role='function', parts=[function_response_part])
                                    )
                                    
                                    iteration += 1
                                    break  # Process one function call at a time
                                else:
                                    log.error(f'[{session_id}] Tool execution requested but no repo_tools available')
                                    break
                        
                        if has_function_call:
                            continue  # Continue the loop for next iteration
                
                # No function calls and no text - something went wrong
                if not has_function_call:
                    log.warning(f'[{session_id}] ⚠️  No function calls and no text at iteration {iteration}')
                    # Try to get partial text
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content is not None and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    log.info(f'[{session_id}] Found partial text: {part.text[:200]}')
                                    return part.text
                    break
            
            # If we exhausted iterations
            log.warning(f'[{session_id}] ⚠️  Reached max iterations ({max_iterations})')
            if hasattr(response, 'text') and response.text:
                return response.text
            else:
                return f'Analysis incomplete after {max_iterations} iterations. Please try again with a simpler request.'
                
        except Exception as e:
            session_id = getattr(self, 'session_id', 'unknown')
            log.error(f'[{session_id}] ❌ Generation failed: {e}')
            import traceback
            traceback.print_exc()
            raise
    
    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool call"""
        if not self.repo_tools:
            return {'error': 'No tools available'}
        
        try:
            if tool_name == 'listTree':
                return self.repo_tools.list_tree(args.get('path', '.'))
            elif tool_name == 'readFile':
                return self.repo_tools.read_file(
                    args.get('path'),
                    args.get('offset', 0),
                    args.get('limit')
                )
            elif tool_name == 'grep':
                return self.repo_tools.grep(
                    args.get('pattern'),
                    args.get('filePattern'),
                    args.get('maxResults', 1000)
                )
            elif tool_name == 'readSnippet':
                return self.repo_tools.read_snippet(
                    args.get('path'),
                    args.get('startLine'),
                    args.get('endLine')
                )
            else:
                return {'error': f'Unknown tool: {tool_name}'}
        except Exception as e:
            log.error(f'Tool execution failed: {e}')
            return {'error': str(e)}
    
    def stream_generate(self, prompt: str, callbacks: Optional[Dict[str, Callable]] = None) -> str:
        """
        Generate with streaming support
        
        Args:
            prompt: User prompt
            callbacks: Optional callbacks for streaming events
            
        Returns:
            Complete generated text
        """
        callbacks = callbacks or {}
        on_text = callbacks.get('on_text', lambda x: None)
        on_tool = callbacks.get('on_tool', lambda name, args: None)
        
        log.info('Starting streaming generation')
        
        try:
            chat = self.model.start_chat(history=[])
            response = chat.send_message(prompt, stream=True)
            
            full_text = ''
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    on_text(chunk.text)
            
            log.info(f'Streaming complete, {len(full_text)} characters')
            return full_text
            
        except Exception as e:
            log.error(f'Streaming failed: {e}')
            raise
