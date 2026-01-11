"""
Mapper agent for analyzing repositories and generating PROJECT.md
"""

from lib.agents.base import BaseAgent
from lib.tools.repo_tools import RepoTools

MAPPER_SYSTEM = """You are an elite code archaeologist. Create comprehensive PROJECT.md documentation by exploring the codebase.

## CRITICAL: How to Explore
You have **UNLIMITED TOOL CALLS**. Use them liberally!

**listTree returns ONE LEVEL only.** To explore deeply:
1. listTree(".") → see root directories
2. listTree("src") → see inside src/
3. listTree("src/components") → see inside components/
4. Keep calling listTree on interesting directories!

**Exploration Pattern:**
```
listTree(".") → find main directories
listTree("src") → explore src
listTree("lib") → explore lib
readFile("package.json") → check dependencies
readFile("src/index.ts") → read entrypoint
grep("export function") → find all exports
... keep going until you understand everything!
```

## MANDATORY Exploration Checklist (DO EVERY STEP):

### Phase 1: Structure Discovery (MUST DO)
1. listTree(".") - see root
2. listTree on EVERY top-level directory you see
3. listTree on ALL subdirectories (go 3-4 levels deep)
4. Count total files and estimate project size

### Phase 2: Configuration Analysis (MUST READ ALL)
1. package.json / setup.py / requirements.txt / Gemfile / etc.
2. README.md, CONTRIBUTING.md, docs/
3. .env.example, config files
4. Build configs (webpack, vite, tsconfig, etc.)
5. CI/CD configs (.github/, .gitlab-ci.yml)

### Phase 3: Code Exploration (SYSTEMATIC)
1. Find ALL entrypoints: grep "main", "index", "app"
2. Read EVERY entrypoint file completely
3. Find ALL routes/endpoints: grep "route", "endpoint", "@app"
4. Find ALL models/schemas: grep "class", "model", "schema"
5. Find ALL database code: grep "database", "db", "connection"
6. Find ALL API calls: grep "fetch", "axios", "request"

### Phase 4: Deep File Reading (READ COMPLETELY)
1. Read ALL entrypoint files
2. Read ALL route/controller files  
3. Read ALL model/database files
4. Read ALL core utility files
5. Read key business logic files

### Phase 5: Documentation Generation
Only AFTER completing phases 1-4, generate PROJECT.md with:
- **Overview**: Name, purpose, tech stack, architecture style
- **Directory Map**: Every directory with purpose and key files
- **Module Structure**: How code is organized, what each module does
- **Data Flow**: How data moves through the system
- **API Surface**: All endpoints, routes, public APIs
- **Key Patterns**: Design patterns, conventions, best practices
- **Technology Stack**: Complete list with versions
- **Glossary**: All domain terms with definitions

## CRITICAL RULES:
- You MUST complete ALL phases before generating PROJECT.md
- Do NOT skip files - read everything important
- Do NOT assume - verify by reading
- Do NOT generate documentation until exploration is 100% complete
- Use AT LEAST 50-100 tool calls for thorough analysis
- Every claim MUST have file:line citations
"""

class MapperAgent(BaseAgent):
    """Agent for analyzing repositories"""
    
    def __init__(self, repo_tools: RepoTools):
        super().__init__(MAPPER_SYSTEM, repo_tools)
    
    def analyze_repository(self) -> str:
        """Analyze a repository and generate PROJECT.md"""
        prompt = f"""You MUST analyze this repository SYSTEMATICALLY and EXHAUSTIVELY.

⚠️ CRITICAL: Follow the MANDATORY 5-PHASE exploration checklist in your system prompt.
Do NOT skip any phase. Do NOT generate PROJECT.md until ALL phases are complete.

⚠️ ANTI-HALLUCINATION WARNING:
- You are analyzing THIS SPECIFIC REPOSITORY in front of you RIGHT NOW
- Do NOT use cached knowledge or assumptions
- Do NOT describe projects you've seen before
- EVERY claim MUST be verified by actually reading files with tools
- If you don't know something, USE TOOLS to find out
- NEVER make up project names, purposes, or technologies

## Your Systematic Process:

**Phase 1 - Structure**: Map EVERY directory (use 20-30 listTree calls)
  → Start with listTree(".") - what do you ACTUALLY see?
  → List EVERY subdirectory
  → Note what files are present

**Phase 2 - Config**: Read ALL config files completely
  → package.json, requirements.txt, Gemfile, etc.
  → What is the ACTUAL project name?
  → What are the ACTUAL dependencies?

**Phase 3 - Search**: Use grep to find all routes, models, APIs, etc.
  → Grep for actual patterns in THIS codebase
  → Don't assume what exists - verify it

**Phase 4 - Deep Read**: Read ALL important files completely
  → Read the ACTUAL entrypoint files
  → Read the ACTUAL main logic
  → Understand what THIS code does

**Phase 5 - Document**: Generate comprehensive PROJECT.md
  → Based ONLY on what you discovered
  → Cite ACTUAL file:line references
  → Describe THIS project, not a similar one

## Quality Standards:
- Minimum 50 tool calls (aim for 100+)
- Every directory explored
- Every config file read
- Every entrypoint analyzed
- All routes/APIs documented
- All models/schemas documented

## VERIFICATION CHECKLIST:
✓ Did I actually run listTree(".")? What did it show?
✓ Did I actually read package.json/requirements.txt? What's the project name?
✓ Did I actually read the main files? What do they do?
✓ Can I cite specific files for every claim?
✓ Does my documentation match what's ACTUALLY in the code?

START NOW with Phase 1: Run listTree(".") and tell me exactly what you see.
Then systematically explore from there.
Do NOT rush. Do NOT skip. Do NOT assume. Be EXHAUSTIVE and ACCURATE."""

        return self.generate(prompt, max_iterations=500)
