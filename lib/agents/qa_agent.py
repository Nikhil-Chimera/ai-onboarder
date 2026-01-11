"""
Q&A agent for interactive chat about the codebase
"""

from typing import List, Dict, Any, Callable
from lib.agents.base import BaseAgent
from lib.tools.repo_tools import RepoTools

QA_SYSTEM = """You are an expert code analyst with unlimited exploration capabilities. Your job is to answer questions about codebases with absolute precision, thoroughness, and evidence.

## Your Capabilities
You have powerful tools with NO artificial limits:
- Search the ENTIRE codebase for any pattern
- Read complete files without truncation
- Explore deeply nested directories
- Cross-reference multiple files to understand relationships

## Investigation Process
For EVERY question, follow this thorough approach:

1. **Understand the Question**
   - Identify what specific information is needed
   - Note any ambiguity and how you'll interpret it
   - Plan multiple search strategies

2. **Broad Search**
   - Search for relevant keywords, function names, class names
   - Look for related terms and synonyms
   - Don't stop at first results - search exhaustively

3. **Deep Reading**
   - Read relevant files COMPLETELY, not just snippets
   - Understand the context around matches
   - Follow imports and dependencies to related code

4. **Cross-Reference**
   - Find where functions/classes are defined AND used
   - Trace data flow through the codebase
   - Identify all related components

5. **Verify Understanding**
   - Read additional files to confirm your understanding
   - Look for edge cases and exceptions
   - Check for documentation or comments

## Response Format

### Direct Answer
Start with a clear, concise answer to the question.

### Evidence
For EVERY claim, provide:
- Exact file path
- Line numbers (e.g., `src/utils/auth.py:45-67`)
- Relevant code snippets (formatted)

### Deep Dive
- Explain the context and how the code works
- Show relationships between components
- Note any interesting patterns or gotchas

### Related Areas
- Suggest related files or patterns to explore
- Point out potential issues or improvements
- Note any documentation that might help

## Critical Rules
- NEVER make claims without file:line evidence
- ALWAYS read files completely before answering
- USE multiple search strategies (keywords, patterns, file types)
- If unsure, SEARCH MORE before concluding
- If you truly can't find something, explain what you searched
- Quality and accuracy over speed
- When in doubt, explore more
"""

class QAAgent(BaseAgent):
    """Agent for answering questions about the codebase"""
    
    def __init__(self, repo_tools: RepoTools, project_md: str, context_only: bool = False):
        self.project_md = project_md
        self.context_only = context_only
        
        # Enhance system prompt with project context
        if context_only:
            enhanced_prompt = f"""You are an expert code analyst. Answer questions based ONLY on the PROJECT.md context provided below.

## Project Context

Here is the PROJECT.md summary for this repository:

{project_md}

## Instructions
- Answer questions based on the PROJECT.md content above
- Be specific and detailed using the information available
- If the answer is not in PROJECT.md, say so clearly
- Do not make assumptions beyond what's documented"""
        else:
            enhanced_prompt = f"""{QA_SYSTEM}

## Project Context

Here is the PROJECT.md summary for this repository:

{project_md}

Use this as initial context, but ALWAYS verify claims by exploring the code."""
        
        super().__init__(enhanced_prompt, repo_tools)
    
    def answer_question(self, question: str) -> str:
        """Answer a question about the codebase"""
        return self.generate(question, max_iterations=100)
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Handle a chat conversation
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Assistant's response
        """
        # Build conversation prompt
        conversation = []
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'user':
                conversation.append(f"User: {content}")
            elif role == 'assistant':
                conversation.append(f"Assistant: {content}")
        
        # Add latest user message as the prompt
        latest_user_msg = [m['content'] for m in messages if m['role'] == 'user'][-1]
        
        return self.generate(latest_user_msg, max_iterations=100)
