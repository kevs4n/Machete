#!/usr/bin/env python3
"""
MACHETE Security Monitor
Validates security controls and monitors for vulnerabilities
"""

import os
import sys
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple


class SecurityMonitor:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        
    def log_issue(self, severity: str, component: str, message: str):
        """Log a security issue"""
        self.issues.append({
            'severity': severity,
            'component': component,
            'message': message
        })
        print(f"[{severity}] {component}: {message}")
    
    def check_docker_socket_exposure(self) -> bool:
        """Check if Docker socket is exposed (CRITICAL vulnerability)"""
        compose_files = [
            self.project_root / "docker-compose.yml",
            self.project_root / "docker-compose.dev.yml"
        ]
        
        socket_exposed = False
        for compose_file in compose_files:
            if compose_file.exists():
                try:
                    with open(compose_file, 'r') as f:
                        content = f.read()
                        if '/var/run/docker.sock' in content:
                            self.log_issue(
                                'CRITICAL', 
                                f'{compose_file.name}',
                                'Docker socket exposed - allows container escape!'
                            )
                            socket_exposed = True
                except Exception as e:
                    self.log_issue('ERROR', f'{compose_file.name}', f'Failed to read: {e}')
        
        return socket_exposed
    
    def check_hardcoded_secrets(self) -> bool:
        """Check for hardcoded secrets in compose files"""
        compose_files = [
            self.project_root / "docker-compose.yml",
            self.project_root / "docker-compose.dev.yml",
            self.project_root / "docker-compose.secure.yml"
        ]
        
        secrets_found = False
        secret_patterns = ['password=', 'secret=', 'key=', 'token=']
        
        for compose_file in compose_files:
            if compose_file.exists():
                try:
                    with open(compose_file, 'r') as f:
                        content = f.read().lower()
                        for pattern in secret_patterns:
                            if pattern in content and '_file' not in content:
                                self.log_issue(
                                    'HIGH', 
                                    f'{compose_file.name}',
                                    f'Potential hardcoded secret: {pattern}'
                                )
                                secrets_found = True
                except Exception as e:
                    self.log_issue('ERROR', f'{compose_file.name}', f'Failed to read: {e}')
        
        return secrets_found
    
    def check_volume_mount_security(self) -> bool:
        """Check for insecure volume mounts"""
        docker_service_file = self.project_root / "core/api/app/services/docker_service.py"
        
        if not docker_service_file.exists():
            self.log_issue('ERROR', 'docker_service.py', 'File not found')
            return True
        
        try:
            with open(docker_service_file, 'r') as f:
                content = f.read()
                
                # Check for SecurityError implementation
                if 'class SecurityError' not in content:
                    self.log_issue(
                        'HIGH', 
                        'docker_service.py',
                        'SecurityError class not implemented'
                    )
                    return True
                    
                # Check for path validation
                if '_prepare_volumes' not in content:
                    self.log_issue(
                        'HIGH', 
                        'docker_service.py',
                        'Volume path validation not implemented'
                    )
                    return True
                    
                # Check for path traversal protection
                if 'os.path.abspath' not in content or 'os.path.commonpath' not in content:
                    self.log_issue(
                        'MEDIUM', 
                        'docker_service.py',
                        'Path traversal protection may be incomplete'
                    )
                    
        except Exception as e:
            self.log_issue('ERROR', 'docker_service.py', f'Failed to read: {e}')
            return True
        
        return False
    
    def check_network_isolation(self) -> bool:
        """Check for proper network isolation"""
        secure_compose = self.project_root / "docker-compose.secure.yml"
        
        if not secure_compose.exists():
            self.log_issue('CRITICAL', 'docker-compose.secure.yml', 'Secure compose file not found')
            return True
        
        try:
            with open(secure_compose, 'r') as f:
                compose_data = yaml.safe_load(f)
                
                networks = compose_data.get('networks', {})
                if 'tool-network' not in networks:
                    self.log_issue(
                        'MEDIUM', 
                        'docker-compose.secure.yml',
                        'Tool network isolation not configured'
                    )
                    return True
                    
                # Check if tool network is internal
                tool_network = networks.get('tool-network', {})
                if not tool_network.get('internal', False):
                    self.log_issue(
                        'HIGH', 
                        'docker-compose.secure.yml',
                        'Tool network should be internal (isolated)'
                    )
                    
        except Exception as e:
            self.log_issue('ERROR', 'docker-compose.secure.yml', f'Failed to parse: {e}')
            return True
        
        return False
    
    def check_resource_controls(self) -> bool:
        """Check for resource controls"""
        secure_compose = self.project_root / "docker-compose.secure.yml"
        
        if not secure_compose.exists():
            return True
        
        try:
            with open(secure_compose, 'r') as f:
                content = f.read()
                
                if 'deploy:' not in content or 'resources:' not in content:
                    self.log_issue(
                        'MEDIUM', 
                        'docker-compose.secure.yml',
                        'Resource controls not implemented'
                    )
                    return True
                    
                if 'security_opt:' not in content:
                    self.log_issue(
                        'MEDIUM', 
                        'docker-compose.secure.yml',
                        'Security options not configured'
                    )
                    
        except Exception as e:
            self.log_issue('ERROR', 'docker-compose.secure.yml', f'Failed to read: {e}')
            return True
        
        return False
    
    def check_secrets_externalization(self) -> bool:
        """Check if secrets are properly externalized"""
        secrets_dir = self.project_root / "secrets"
        
        if not secrets_dir.exists():
            self.log_issue('HIGH', 'secrets/', 'Secrets directory not found')
            return True
        
        required_secrets = ['api_secret.txt', 'db_password.txt']
        missing_secrets = []
        
        for secret in required_secrets:
            secret_file = secrets_dir / secret
            if not secret_file.exists():
                missing_secrets.append(secret)
        
        if missing_secrets:
            self.log_issue(
                'HIGH', 
                'secrets/',
                f'Missing secret files: {", ".join(missing_secrets)}'
            )
            return True
        
        # Check if secrets are in .gitignore
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            try:
                with open(gitignore, 'r') as f:
                    gitignore_content = f.read()
                    if 'secrets/' not in gitignore_content:
                        self.log_issue(
                            'HIGH', 
                            '.gitignore',
                            'Secrets directory not excluded from git'
                        )
            except Exception as e:
                self.log_issue('ERROR', '.gitignore', f'Failed to read: {e}')
        
        return False
    
    def check_docker_daemon_isolation(self) -> bool:
        """Check Docker-in-Docker isolation"""
        secure_compose = self.project_root / "docker-compose.secure.yml"
        
        if not secure_compose.exists():
            return True
        
        try:
            with open(secure_compose, 'r') as f:
                content = f.read()
                
                if 'docker:26-dind' not in content:
                    self.log_issue(
                        'HIGH', 
                        'docker-compose.secure.yml',
                        'Docker-in-Docker isolation not implemented'
                    )
                    return True
                    
                if 'DOCKER_TLS_VERIFY' not in content:
                    self.log_issue(
                        'MEDIUM', 
                        'docker-compose.secure.yml',
                        'Docker TLS verification not configured'
                    )
                    
        except Exception as e:
            self.log_issue('ERROR', 'docker-compose.secure.yml', f'Failed to read: {e}')
            return True
        
        return False
    
    def run_security_audit(self) -> Dict[str, bool]:
        """Run complete security audit"""
        print("🔒 MACHETE Security Audit")
        print("=" * 50)
        
        results = {
            'docker_socket_exposed': self.check_docker_socket_exposure(),
            'hardcoded_secrets': self.check_hardcoded_secrets(),
            'volume_mount_insecure': self.check_volume_mount_security(),
            'network_isolation_missing': self.check_network_isolation(),
            'resource_controls_missing': self.check_resource_controls(),
            'secrets_not_externalized': self.check_secrets_externalization(),
            'docker_daemon_not_isolated': self.check_docker_daemon_isolation()
        }
        
        print("\n" + "=" * 50)
        
        # Count issues by severity
        critical = len([i for i in self.issues if i['severity'] == 'CRITICAL'])
        high = len([i for i in self.issues if i['severity'] == 'HIGH'])
        medium = len([i for i in self.issues if i['severity'] == 'MEDIUM'])
        
        print(f"Security Issues Found:")
        print(f"  🔴 Critical: {critical}")
        print(f"  🟠 High: {high}")
        print(f"  🟡 Medium: {medium}")
        
        if critical > 0:
            print("\n⚠️  CRITICAL issues found - DO NOT deploy to production!")
            return_code = 2
        elif high > 0:
            print("\n⚠️  HIGH severity issues found - Review before deployment")
            return_code = 1
        elif medium > 0:
            print("\n✅ Medium severity issues only - Generally safe for deployment")
            return_code = 0
        else:
            print("\n✅ No security issues found - Safe for deployment")
            return_code = 0
        
        return results, return_code


def main():
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    monitor = SecurityMonitor(project_root)
    results, return_code = monitor.run_security_audit()
    
    sys.exit(return_code)


if __name__ == "__main__":
    main()
