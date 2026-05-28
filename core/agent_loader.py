import os
import glob
import subprocess
from typing import List, Dict, Any, Optional

REPOS_DIR = r"D:\Claude\repos"
AGENCY_DIR = os.path.join(REPOS_DIR, "agency-agents")
UI_UX_DIR = os.path.join(REPOS_DIR, "ui-ux-pro-max-skill")
SEARCH_SCRIPT = os.path.join(UI_UX_DIR, "src", "ui-ux-pro-max", "scripts", "search.py")


def search_ui_ux(query: str, domain: Optional[str] = None, stack: Optional[str] = None) -> str:
    """
    Programmatically queries the ui-ux-pro-max BM25 design intelligence database.
    Returns the formatted markdown search results directly to the agent.
    """
    if not os.path.exists(SEARCH_SCRIPT):
        return "[Error] UI/UX Pro Max search engine is not initialized or found."

    cmd = ["python", SEARCH_SCRIPT, query]
    if domain:
        cmd.extend(["--domain", domain])
    if stack:
        cmd.extend(["--stack", stack])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"[Error] UI/UX Pro Max search engine failed: {e.stderr or e.stdout or str(e)}"
    except Exception as e:
        return f"[Error] Failed to run search CLI: {str(e)}"


def list_personas() -> List[str]:
    """
    Scans the agency-agents directory and lists all available persona markdown files.
    """
    if not os.path.exists(AGENCY_DIR):
        return []
    
    # Recursively find all markdown files
    md_files = glob.glob(os.path.join(AGENCY_DIR, "**", "*.md"), recursive=True)
    personas = []
    for f in md_files:
        rel_path = os.path.relpath(f, AGENCY_DIR)
        personas.append(rel_path.replace(os.sep, "/"))
    return sorted(personas)


def load_persona(persona_name: str) -> Optional[str]:
    """
    Reads and returns the complete system prompt instructions of a specific persona.
    Example: load_persona("engineering/backend-architect.md")
    """
    # Clean the path
    clean_name = persona_name.replace("/", os.sep).replace("\\", os.sep)
    target_path = os.path.join(AGENCY_DIR, clean_name)
    
    # Try with .md appended if not present
    if not target_path.lower().endswith(".md") and not os.path.exists(target_path):
        target_path += ".md"
        
    if os.path.exists(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading persona: {e}"
            
    # Fuzzy match by basename
    all_files = glob.glob(os.path.join(AGENCY_DIR, "**", "*.md"), recursive=True)
    for f in all_files:
        if persona_name.lower() in os.path.basename(f).lower():
            try:
                with open(f, "r", encoding="utf-8") as file:
                    return file.read()
            except Exception:
                pass
                
    return None


def match_persona_by_task(task_description: str) -> Optional[Dict[str, Any]]:
    """
    Intelligently scans the task description and automatically resolves the best
    specialized agent persona from agency-agents using keyword/category matching.
    
    Returns a dictionary containing:
        - "persona_path": Relative path of the persona MD file
        - "persona_name": Cleaned name of the role
        - "prompt_content": Complete system prompt text
    """
    if not os.path.exists(AGENCY_DIR):
        return None

    task_lower = task_description.lower()
    
    # Mapping task keywords to specialized persona files
    keyword_mapping = {
        # Backend & Databases
        "database": "engineering-database-optimizer",
        "sql": "engineering-database-optimizer",
        "schema": "engineering-database-optimizer",
        "backend": "engineering-backend-architect",
        "api": "engineering-backend-architect",
        "server": "engineering-backend-architect",
        
        # Security
        "security": "engineering-security-engineer",
        "penetration": "engineering-security-engineer",
        "exploit": "engineering-security-engineer",
        "vulnerability": "engineering-security-engineer",
        "injection": "engineering-security-engineer",
        "threat": "engineering-threat-detection-engineer",
        
        # Frontend, Design & UI
        "frontend": "engineering-frontend-developer",
        "css": "engineering-frontend-developer",
        "style": "design-ui-ux-pro-max",
        "ui": "design-ui-ux-pro-max",
        "ux": "design-ui-ux-pro-max",
        "layout": "design-ui-ux-pro-max",
        
        # Devops, Git & SRE
        "deploy": "engineering-devops-automator",
        "docker": "engineering-devops-automator",
        "ci/cd": "engineering-devops-automator",
        "kubernetes": "engineering-devops-automator",
        "git": "engineering-git-workflow-master",
        "pr": "engineering-git-workflow-master",
        "incident": "engineering-incident-response-commander",
        "sre": "engineering-sre",
        
        # Swarm Orchestration & Autonomous Systems (Ruflo & Hermes Integration)
        "ruflo": "specialized-ruflo-swarm-orchestrator",
        "swarm": "specialized-ruflo-swarm-orchestrator",
        "parallel": "specialized-ruflo-swarm-orchestrator",
        "multi-agent": "specialized-ruflo-swarm-orchestrator",
        "hermes": "specialized-hermes-autonomous-agent",
        "autonomous": "specialized-hermes-autonomous-agent",
        "persistent": "specialized-hermes-autonomous-agent",
        "daemon": "specialized-hermes-autonomous-agent",
        
        # Quality Assurance & Testing
        "test": "testing-qa-engineer",
        "pytest": "testing-qa-engineer",
        "coverage": "testing-qa-engineer",
        
        # Writing & Documentation
        "write": "engineering-technical-writer",
        "doc": "engineering-technical-writer",
        "readme": "engineering-technical-writer",
        
        # Architecture & Software Engineering
        "architecture": "engineering-software-architect",
        "design pattern": "engineering-software-architect",
        "optimize": "engineering-autonomous-optimization-architect",
        "refactor": "engineering-autonomous-optimization-architect",
    }


    selected_base = None
    for kw, base_name in keyword_mapping.items():
        if kw in task_lower:
            selected_base = base_name
            break

    # If no specific keyword matched, default to general software architect or senior developer
    if not selected_base:
        if "design" in task_lower:
            selected_base = "design-ui-ux-pro-max"
        elif "marketing" in task_lower:
            selected_base = "marketing-growth-hacker"
        else:
            selected_base = "engineering-software-architect"

    # Search for the matched file
    all_files = glob.glob(os.path.join(AGENCY_DIR, "**", "*.md"), recursive=True)
    for f in all_files:
        basename = os.path.basename(f)
        if selected_base.lower() in basename.lower():
            try:
                with open(f, "r", encoding="utf-8") as file:
                    content = file.read()
                rel_path = os.path.relpath(f, AGENCY_DIR).replace(os.sep, "/")
                
                # Format name nicely: e.g. "engineering-backend-architect" -> "Backend Architect"
                clean_name = os.path.splitext(basename)[0]
                clean_name = clean_name.replace("engineering-", "").replace("design-", "").replace("testing-", "")
                clean_name = " ".join([w.capitalize() for w in clean_name.split("-")])
                
                return {
                    "persona_path": rel_path,
                    "persona_name": clean_name,
                    "prompt_content": content
                }
            except Exception:
                pass

    return None
