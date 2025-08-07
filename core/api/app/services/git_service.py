"""
Git service for repository management
"""

import asyncio
import shutil
import tempfile
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
try:
    from git import Repo, GitCommandError
except ImportError:
    # Fallback if GitPython is not available
    Repo = None
    GitCommandError = Exception
from app.core.config import settings
from app.core.exceptions import ToolImportError, ValidationError
import logging

logger = logging.getLogger(__name__)

class GitService:
    """Service for Git repository operations with enhanced error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def validate_and_clone_repository(self, git_url: str) -> Dict[str, Any]:
        """
        Enhanced repository validation and cloning with comprehensive error handling
        """
        import_context: Dict[str, Any] = {
            "git_url": git_url,
            "step": "initialization",
            "timestamp": datetime.now().isoformat(),
            "errors": [],
            "warnings": [],
            "metadata": {}
        }
        
        try:
            self.logger.info(f"🔄 Starting tool import from: {git_url}")
            
            # Step 1: Validate Git URL format
            import_context["step"] = "url_validation"
            self.logger.info(f"📋 Step 1: Validating Git URL format")
            
            if not self._is_valid_git_url(git_url):
                raise ToolImportError(
                    f"Invalid Git URL format: {git_url}",
                    "INVALID_GIT_URL",
                    {"git_url": git_url, "expected_formats": ["https://", "git@", "file://"]}
                )
            
            # Step 2: Check repository accessibility
            import_context["step"] = "repository_accessibility"
            self.logger.info(f"🔗 Step 2: Checking repository accessibility")
            
            accessibility_result = await self._check_repository_accessibility(git_url)
            if not accessibility_result["accessible"]:
                raise ToolImportError(
                    f"Repository not accessible: {accessibility_result['error']}",
                    "REPOSITORY_INACCESSIBLE",
                    accessibility_result
                )
            
            # Step 3: Clone repository
            import_context["step"] = "cloning"
            self.logger.info(f"📥 Step 3: Cloning repository")
            
            clone_result = await self._clone_repository_safe(git_url)
            repo_path = clone_result["repo_path"]
            import_context["metadata"]["repo_path"] = str(repo_path)
            
            # Step 4: Validate tool structure
            import_context["step"] = "structure_validation"
            self.logger.info(f"🔍 Step 4: Validating tool structure")
            
            structure_validation = await self._validate_tool_structure(repo_path)
            if not structure_validation["valid"]:
                if "warnings" in structure_validation:
                    import_context["warnings"].extend(structure_validation["warnings"])
                if structure_validation["critical_errors"]:
                    raise ToolImportError(
                        "Tool structure validation failed",
                        "INVALID_TOOL_STRUCTURE",
                        structure_validation
                    )
            
            # Step 5: Extract metadata
            import_context["step"] = "metadata_extraction"
            self.logger.info(f"📊 Step 5: Extracting tool metadata")
            
            metadata = await self.extract_tool_metadata_enhanced(repo_path)
            import_context["metadata"].update(metadata)
            
            # Step 6: Validate Docker configuration
            import_context["step"] = "docker_validation"
            self.logger.info(f"🐳 Step 6: Validating Docker configuration")
            
            docker_validation = await self._validate_docker_configuration(repo_path, metadata)
            if not docker_validation["valid"]:
                if "errors" in docker_validation:
                    import_context["errors"].extend(docker_validation["errors"])
                if "warnings" in docker_validation:
                    import_context["warnings"].extend(docker_validation["warnings"])
            
            # Step 7: Final validation
            import_context["step"] = "final_validation"
            self.logger.info(f"✅ Step 7: Final validation")
            
            final_result: Dict[str, Any] = {
                "success": True,
                "repo_path": str(repo_path),
                "metadata": metadata,
                "import_context": import_context,
                "docker_config": docker_validation
            }
            
            self.logger.info(f"🎉 Tool import successful: {metadata.get('name', 'unknown')}")
            return final_result
            
        except ToolImportError as e:
            self.logger.error(f"❌ Tool import failed at step '{import_context['step']}': {e.message}")
            import_context["errors"].append({
                "step": import_context["step"],
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details,
                "traceback": traceback.format_exc()
            })
            
            return {
                "success": False,
                "error": e.message,
                "error_code": e.error_code,
                "import_context": import_context,
                "troubleshooting": self._generate_troubleshooting_guide(e.error_code, e.details)
            }
            
        except Exception as e:
            self.logger.error(f"💥 Unexpected error during tool import: {str(e)}")
            import_context["errors"].append({
                "step": import_context["step"],
                "error_code": "UNEXPECTED_ERROR",
                "message": str(e),
                "traceback": traceback.format_exc()
            })
            
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_code": "UNEXPECTED_ERROR",
                "import_context": import_context,
                "troubleshooting": self._generate_troubleshooting_guide("UNEXPECTED_ERROR", {"error": str(e)})
            }
    
    async def _check_repository_accessibility(self, git_url: str) -> Dict[str, Any]:
        """Check if repository is accessible"""
        try:
            self.logger.info(f"🔍 Checking accessibility of: {git_url}")
            
            # Use git ls-remote to check accessibility
            result = subprocess.run(
                ["git", "ls-remote", "--heads", git_url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info(f"✅ Repository accessible: {git_url}")
                return {
                    "accessible": True,
                    "remote_refs": result.stdout.strip().split('\n') if result.stdout.strip() else []
                }
            else:
                self.logger.warning(f"⚠️ Repository not accessible: {result.stderr}")
                return {
                    "accessible": False,
                    "error": result.stderr.strip(),
                    "return_code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout while checking repository accessibility (30s limit)"
            self.logger.error(f"⏰ {error_msg}")
            return {
                "accessible": False,
                "error": error_msg,
                "return_code": "TIMEOUT"
            }
        except FileNotFoundError:
            error_msg = "Git command not found. Please ensure Git is installed."
            self.logger.error(f"❌ {error_msg}")
            return {
                "accessible": False,
                "error": error_msg,
                "return_code": "GIT_NOT_FOUND"
            }
        except Exception as e:
            error_msg = f"Unexpected error checking repository: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                "accessible": False,
                "error": error_msg,
                "return_code": "UNEXPECTED_ERROR"
            }
    
    async def _clone_repository_safe(self, git_url: str) -> Dict[str, Any]:
        """Safely clone repository with comprehensive error handling"""
        temp_dir = None
        try:
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix="machete_tool_"))
            self.logger.info(f"📁 Created temporary directory: {temp_dir}")
            
            # Clone repository
            self.logger.info(f"📥 Cloning repository to: {temp_dir}")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", git_url, str(temp_dir / "repo")],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                repo_path = temp_dir / "repo"
                self.logger.info(f"✅ Repository cloned successfully to: {repo_path}")
                return {
                    "success": True,
                    "repo_path": repo_path,
                    "clone_output": result.stdout
                }
            else:
                self.logger.error(f"❌ Git clone failed: {result.stderr}")
                raise ToolImportError(
                    f"Failed to clone repository: {result.stderr}",
                    "CLONE_FAILED",
                    {
                        "git_url": git_url,
                        "return_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                )
                
        except subprocess.TimeoutExpired:
            error_msg = "Repository clone timeout (5 minute limit exceeded)"
            self.logger.error(f"⏰ {error_msg}")
            raise ToolImportError(error_msg, "CLONE_TIMEOUT", {"git_url": git_url})
            
        except Exception as e:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise
    
    async def _validate_tool_structure(self, repo_path: Path) -> Dict[str, Any]:
        """Validate tool repository structure"""
        validation_result: Dict[str, Any] = {
            "valid": True,
            "warnings": [],
            "critical_errors": [],
            "found_files": [],
            "structure_score": 0
        }
        
        try:
            self.logger.info(f"🔍 Validating tool structure in: {repo_path}")
            
            # Check for essential files
            essential_files: Dict[str, Dict[str, Any]] = {
                "Dockerfile": {"required": True, "score": 30},
                "machete.yml": {"required": False, "score": 20},
                "docker-compose.yml": {"required": False, "score": 15},
                "README.md": {"required": False, "score": 10},
                "package.json": {"required": False, "score": 5},
                "requirements.txt": {"required": False, "score": 5},
                "pyproject.toml": {"required": False, "score": 5}
            }
            
            for filename, config in essential_files.items():
                file_path = repo_path / filename
                if file_path.exists():
                    validation_result["found_files"].append(filename)
                    validation_result["structure_score"] += config["score"]
                    self.logger.info(f"✅ Found: {filename}")
                elif config["required"]:
                    error_msg = f"Required file missing: {filename}"
                    validation_result["critical_errors"].append(error_msg)
                    self.logger.error(f"❌ {error_msg}")
                else:
                    validation_result["warnings"].append(f"Optional file missing: {filename}")
                    self.logger.warning(f"⚠️ Optional file missing: {filename}")
            
            # Check for basic project structure
            if not validation_result["critical_errors"]:
                validation_result["valid"] = True
                self.logger.info(f"✅ Tool structure valid (score: {validation_result['structure_score']}/100)")
            else:
                validation_result["valid"] = False
                self.logger.error(f"❌ Tool structure invalid: {validation_result['critical_errors']}")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"💥 Error validating tool structure: {str(e)}")
            validation_result["valid"] = False
            validation_result["critical_errors"].append(f"Validation error: {str(e)}")
            return validation_result
    
    async def _validate_docker_configuration(self, repo_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Docker configuration"""
        docker_validation: Dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "dockerfile_analysis": {},
            "compose_analysis": {}
        }
        
        try:
            self.logger.info(f"🐳 Validating Docker configuration")
            
            # Analyze Dockerfile
            dockerfile_path = repo_path / "Dockerfile"
            if dockerfile_path.exists():
                dockerfile_analysis = await self._analyze_dockerfile(dockerfile_path)
                docker_validation["dockerfile_analysis"] = dockerfile_analysis
                
                if not dockerfile_analysis["valid"]:
                    docker_validation["errors"].extend(dockerfile_analysis["errors"])
                if dockerfile_analysis.get("warnings"):
                    docker_validation["warnings"].extend(dockerfile_analysis["warnings"])
            
            # Analyze docker-compose.yml
            compose_path = repo_path / "docker-compose.yml"
            if compose_path.exists():
                compose_analysis = await self._analyze_compose_file(compose_path)
                docker_validation["compose_analysis"] = compose_analysis
                
                if not compose_analysis["valid"]:
                    docker_validation["errors"].extend(compose_analysis["errors"])
                if compose_analysis.get("warnings"):
                    docker_validation["warnings"].extend(compose_analysis["warnings"])
            
            docker_validation["valid"] = len(docker_validation["errors"]) == 0
            
            return docker_validation
            
        except Exception as e:
            self.logger.error(f"💥 Error validating Docker configuration: {str(e)}")
            docker_validation["valid"] = False
            docker_validation["errors"].append(f"Docker validation error: {str(e)}")
            return docker_validation
    
    async def _analyze_dockerfile(self, dockerfile_path: Path) -> Dict[str, Any]:
        """Analyze Dockerfile for common issues"""
        analysis = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "base_image": None,
            "exposed_ports": [],
            "has_entrypoint": False,
            "has_cmd": False
        }
        
        try:
            content = dockerfile_path.read_text(encoding='utf-8')
            lines = content.strip().split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Check FROM instruction
                if line.upper().startswith('FROM'):
                    analysis["base_image"] = line.split()[1] if len(line.split()) > 1 else None
                
                # Check EXPOSE instructions
                elif line.upper().startswith('EXPOSE'):
                    ports = line.split()[1:] if len(line.split()) > 1 else []
                    analysis["exposed_ports"].extend(ports)
                
                # Check for ENTRYPOINT
                elif line.upper().startswith('ENTRYPOINT'):
                    analysis["has_entrypoint"] = True
                
                # Check for CMD
                elif line.upper().startswith('CMD'):
                    analysis["has_cmd"] = True
            
            # Validation checks
            if not analysis["base_image"]:
                analysis["errors"].append("No FROM instruction found in Dockerfile")
            
            if not analysis["has_entrypoint"] and not analysis["has_cmd"]:
                analysis["warnings"].append("No ENTRYPOINT or CMD instruction found")
            
            if not analysis["exposed_ports"]:
                analysis["warnings"].append("No EXPOSE instruction found - tool may not be accessible")
            
            analysis["valid"] = len(analysis["errors"]) == 0
            
        except Exception as e:
            analysis["valid"] = False
            analysis["errors"].append(f"Error analyzing Dockerfile: {str(e)}")
        
        return analysis
    
    async def _analyze_compose_file(self, compose_path: Path) -> Dict[str, Any]:
        """Analyze docker-compose.yml for common issues"""
        analysis = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "services": [],
            "networks": [],
            "volumes": []
        }
        
        try:
            import yaml
            
            content = compose_path.read_text(encoding='utf-8')
            compose_data = yaml.safe_load(content)
            
            # Extract services
            if 'services' in compose_data:
                analysis["services"] = list(compose_data['services'].keys())
            else:
                analysis["errors"].append("No 'services' section found in docker-compose.yml")
            
            # Extract networks
            if 'networks' in compose_data:
                analysis["networks"] = list(compose_data['networks'].keys())
            
            # Extract volumes
            if 'volumes' in compose_data:
                analysis["volumes"] = list(compose_data['volumes'].keys())
            
            # Validation checks
            if not analysis["services"]:
                analysis["errors"].append("No services defined in docker-compose.yml")
            
            analysis["valid"] = len(analysis["errors"]) == 0
            
        except Exception as e:
            analysis["valid"] = False
            analysis["errors"].append(f"Invalid YAML in docker-compose.yml: {str(e)}")
        
        return analysis
    
    def _generate_troubleshooting_guide(self, error_code: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Generate contextual troubleshooting guide"""
        guides = {
            "INVALID_GIT_URL": {
                "description": "The provided Git URL format is invalid",
                "common_causes": [
                    "URL doesn't start with https://, git@, or file://",
                    "Typo in the repository URL",
                    "Missing .git extension for some providers"
                ],
                "solutions": [
                    "Ensure URL starts with https:// (e.g., https://github.com/user/repo.git)",
                    "For SSH: git@github.com:user/repo.git", 
                    "For local files: file:///path/to/repo",
                    "Double-check the repository URL on the provider's website"
                ]
            },
            "REPOSITORY_INACCESSIBLE": {
                "description": "The repository cannot be accessed",
                "common_causes": [
                    "Repository is private and requires authentication",
                    "Repository doesn't exist or was moved",
                    "Network connectivity issues",
                    "Git is not installed on the system"
                ],
                "solutions": [
                    "Verify the repository exists and is public",
                    "Check your internet connection",
                    "For private repos, ensure you have access credentials configured",
                    "Install Git if missing: apt-get install git (Linux) or download from git-scm.com"
                ]
            },
            "CLONE_FAILED": {
                "description": "Repository cloning failed",
                "common_causes": [
                    "Network timeout or slow connection",
                    "Large repository size",
                    "Authentication required",
                    "Insufficient disk space"
                ],
                "solutions": [
                    "Try again with a better network connection",
                    "Check available disk space",
                    "For large repos, consider using --depth 1 for shallow clone",
                    "Verify repository access permissions"
                ]
            },
            "INVALID_TOOL_STRUCTURE": {
                "description": "Tool repository structure doesn't meet requirements",
                "common_causes": [
                    "Missing required Dockerfile",
                    "No executable entry point defined",
                    "Incorrect file permissions"
                ],
                "solutions": [
                    "Add a Dockerfile to define the container build",
                    "Include a machete.yml file for tool configuration",
                    "Ensure all required files are present",
                    "Check the MACHETE tool template for examples"
                ]
            }
        }
        
        return guides.get(error_code, {
            "description": "An unexpected error occurred",
            "solutions": [
                "Check the error details in the logs",
                "Verify all prerequisites are met",
                "Contact support if the issue persists"
            ]
        })
    
    def _is_valid_git_url(self, url: str) -> bool:
        """Validate Git URL format"""
        valid_prefixes = ['https://', 'http://', 'git@', 'file://']
        return any(url.startswith(prefix) for prefix in valid_prefixes)
    
    async def extract_tool_metadata_enhanced(self, repo_path: str) -> Dict[str, Any]:
        """Enhanced tool metadata extraction with error handling"""
        try:
            metadata = await self.extract_tool_metadata(repo_path)
            return metadata
        except Exception as e:
            self.logger.error(f"Error in enhanced metadata extraction: {str(e)}")
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
