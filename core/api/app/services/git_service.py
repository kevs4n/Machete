"""
Git service for repository management
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from git import Repo, GitCommandError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class GitService:
    """Service for Git repository operations"""
    
    async def clone_repository(self, git_url: str, branch: str = "main") -> Dict[str, Any]:
        """Clone a Git repository"""
        temp_dir = None
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="machete-clone-")
            
            # Clone repository
            repo = Repo.clone_from(
                git_url,
                temp_dir,
                branch=branch,
                depth=settings.GIT_CLONE_DEPTH,
                timeout=settings.GIT_CLONE_TIMEOUT
            )
            
            # Get commit information
            commit_hash = repo.head.commit.hexsha
            commit_message = repo.head.commit.message.strip()
            author = str(repo.head.commit.author)
            
            return {
                "success": True,
                "path": temp_dir,
                "commit_hash": commit_hash,
                "commit_message": commit_message,
                "author": author,
                "branch": branch
            }
            
        except GitCommandError as e:
            logger.error(f"Git clone failed for {git_url}: {e}")
            if temp_dir and Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "success": False,
                "error": str(e),
                "path": None
            }
        except Exception as e:
            logger.error(f"Unexpected error cloning {git_url}: {e}")
            if temp_dir and Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "success": False,
                "error": str(e),
                "path": None
            }
    
    async def update_repository(self, repo_path: str, branch: str = "main") -> Dict[str, Any]:
        """Update an existing repository"""
        try:
            repo = Repo(repo_path)
            
            # Fetch latest changes
            origin = repo.remotes.origin
            origin.fetch()
            
            # Get current commit before update
            old_commit = repo.head.commit.hexsha
            
            # Reset to latest
            origin.refs[branch].checkout(force=True)
            repo.head.reset(index=True, working_tree=True)
            
            # Get new commit information
            new_commit = repo.head.commit.hexsha
            commit_message = repo.head.commit.message.strip()
            author = str(repo.head.commit.author)
            
            updated = old_commit != new_commit
            
            return {
                "success": True,
                "updated": updated,
                "old_commit": old_commit,
                "new_commit": new_commit,
                "commit_message": commit_message,
                "author": author
            }
            
        except GitCommandError as e:
            logger.error(f"Git update failed for {repo_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "updated": False
            }
        except Exception as e:
            logger.error(f"Unexpected error updating {repo_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "updated": False
            }
    
    async def validate_repository(self, git_url: str, branch: str = "main") -> Dict[str, Any]:
        """Validate that a repository exists and is accessible"""
        try:
            # Use ls-remote to check if repository exists without cloning
            from git.cmd import Git
            git = Git()
            
            # This will raise an exception if repository doesn't exist
            refs = git.ls_remote(git_url, heads=True)
            
            # Check if the specified branch exists
            branch_exists = any(f"refs/heads/{branch}" in ref for ref in refs.split('\n'))
            
            return {
                "success": True,
                "exists": True,
                "branch_exists": branch_exists,
                "url": git_url,
                "branch": branch
            }
            
        except GitCommandError as e:
            logger.error(f"Repository validation failed for {git_url}: {e}")
            return {
                "success": False,
                "exists": False,
                "branch_exists": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error validating {git_url}: {e}")
            return {
                "success": False,
                "exists": False,
                "branch_exists": False,
                "error": str(e)
            }
    
    async def get_repository_info(self, repo_path: str) -> Dict[str, Any]:
        """Get information about a local repository"""
        try:
            repo = Repo(repo_path)
            
            # Get current branch
            current_branch = repo.active_branch.name
            
            # Get commit information
            commit = repo.head.commit
            commit_hash = commit.hexsha
            commit_message = commit.message.strip()
            author = str(commit.author)
            commit_date = commit.committed_datetime.isoformat()
            
            # Get remote URL
            remote_url = None
            if repo.remotes:
                remote_url = repo.remotes.origin.url
            
            # Check if there are uncommitted changes
            is_dirty = repo.is_dirty()
            
            return {
                "success": True,
                "branch": current_branch,
                "commit_hash": commit_hash,
                "commit_message": commit_message,
                "author": author,
                "commit_date": commit_date,
                "remote_url": remote_url,
                "has_changes": is_dirty
            }
            
        except Exception as e:
            logger.error(f"Error getting repository info for {repo_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup_repository(self, repo_path: str) -> bool:
        """Clean up a cloned repository"""
        try:
            if repo_path and Path(repo_path).exists():
                shutil.rmtree(repo_path, ignore_errors=True)
                return True
            return True
        except Exception as e:
            logger.error(f"Error cleaning up repository {repo_path}: {e}")
            return False
    
    async def extract_tool_metadata(self, repo_path: str) -> Dict[str, Any]:
        """Extract tool metadata from repository"""
        try:
            repo_dir = Path(repo_path)
            metadata = {
                "name": None,
                "description": None,
                "version": None,
                "author": None,
                "license": None,
                "dockerfile_path": "Dockerfile",
                "has_dockerfile": False,
                "port": None,
                "health_check": "/health"
            }
            
            # Check for Dockerfile
            dockerfile_paths = ["Dockerfile", "docker/Dockerfile", "build/Dockerfile"]
            for path in dockerfile_paths:
                if (repo_dir / path).exists():
                    metadata["dockerfile_path"] = path
                    metadata["has_dockerfile"] = True
                    break
            
            # Check for Docker Compose files
            compose_files = ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]
            for compose_file in compose_files:
                if (repo_dir / compose_file).exists():
                    metadata["has_compose"] = True
                    metadata["compose_file"] = compose_file
                    break
            else:
                metadata["has_compose"] = False
                metadata["compose_file"] = None
            
            # Check for package.json (Node.js)
            package_json = repo_dir / "package.json"
            if package_json.exists():
                import json
                with open(package_json) as f:
                    data = json.load(f)
                    metadata["name"] = data.get("name")
                    metadata["description"] = data.get("description")
                    metadata["version"] = data.get("version")
                    metadata["author"] = data.get("author")
                    metadata["license"] = data.get("license")
            
            # Check for requirements.txt or pyproject.toml (Python)
            if (repo_dir / "requirements.txt").exists() or (repo_dir / "pyproject.toml").exists():
                # Try to find Flask/FastAPI port configuration
                for file_path in repo_dir.rglob("*.py"):
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if "app.run" in content and "port=" in content:
                            # Extract port from Flask app.run
                            import re
                            match = re.search(r'port=(\d+)', content)
                            if match:
                                metadata["port"] = int(match.group(1))
                                break
                        elif "uvicorn" in content and "port=" in content:
                            # Extract port from uvicorn
                            import re
                            match = re.search(r'port=(\d+)', content)
                            if match:
                                metadata["port"] = int(match.group(1))
                                break
                    except Exception:
                        continue
            
            # Check for machete.yml configuration
            machete_yml = repo_dir / "machete.yml"
            if machete_yml.exists():
                try:
                    import yaml
                    with open(machete_yml) as f:
                        machete_config = yaml.safe_load(f)
                    
                    # Extract basic metadata
                    if not metadata["name"]:
                        metadata["name"] = machete_config.get("name")
                    if not metadata["description"]:
                        metadata["description"] = machete_config.get("description")
                    if not metadata["version"]:
                        metadata["version"] = machete_config.get("version")
                    if not metadata["author"]:
                        metadata["author"] = machete_config.get("author")
                    if not metadata["license"]:
                        metadata["license"] = machete_config.get("license")
                    
                    # Extract MACHETE-specific configuration
                    machete_settings = machete_config.get("machete", {})
                    if not metadata["port"]:
                        metadata["port"] = machete_settings.get("port")
                    if machete_settings.get("health_check"):
                        metadata["health_check"] = machete_settings["health_check"]
                    
                    # Extract volumes configuration
                    volumes = machete_settings.get("volumes", [])
                    if volumes:
                        metadata["volumes"] = volumes
                    
                    # Extract environment variables
                    environment = machete_settings.get("environment", [])
                    if environment:
                        metadata["environment"] = environment
                    
                    # Extract dependencies
                    dependencies = machete_settings.get("dependencies", [])
                    if dependencies:
                        metadata["dependencies"] = dependencies
                        
                except Exception as e:
                    logger.warning(f"Failed to parse machete.yml: {e}")
            
            # Check for README files
            readme_files = ["README.md", "README.txt", "README.rst", "readme.md"]
            for readme in readme_files:
                readme_path = repo_dir / readme
                if readme_path.exists():
                    try:
                        content = readme_path.read_text(encoding='utf-8', errors='ignore')
                        if not metadata["description"] and len(content) > 10:
                            # Extract first paragraph as description
                            lines = content.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line and not line.startswith('#') and len(line) > 20:
                                    metadata["description"] = line[:200]
                                    break
                        break
                    except Exception:
                        continue
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {repo_path}: {e}")
            return {
                "name": None,
                "description": None,
                "version": None,
                "author": None,
                "license": None,
                "dockerfile_path": "Dockerfile",
                "has_dockerfile": False,
                "port": None,
                "health_check": "/health"
            }
