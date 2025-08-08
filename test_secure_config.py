#!/usr/bin/env python3
"""
Test security of the secure Docker Compose configuration
"""
import yaml
import sys

def test_secure_compose():
    """Test the security of docker-compose.secure.yml"""
    print("🔒 Testing Secure Configuration")
    print("=" * 50)
    
    issues = []
    
    try:
        with open('docker-compose.secure.yml', 'r') as f:
            compose = yaml.safe_load(f)
            
        # Check for Docker socket exposure
        socket_found = False
        for service_name, service in compose.get('services', {}).items():
            volumes = service.get('volumes', [])
            for volume in volumes:
                if isinstance(volume, str) and '/var/run/docker.sock' in volume:
                    issues.append(f"❌ {service_name}: Docker socket still exposed!")
                    socket_found = True
                elif isinstance(volume, dict) and '/var/run/docker.sock' in str(volume):
                    issues.append(f"❌ {service_name}: Docker socket still exposed!")
                    socket_found = True
        
        if not socket_found:
            print("✅ Docker socket exposure: FIXED")
        
        # Check for Docker-in-Docker implementation
        dind_found = False
        for service_name, service in compose.get('services', {}).items():
            image = service.get('image', '')
            if 'dind' in image or 'docker:' in image:
                print(f"✅ Docker-in-Docker: Found service '{service_name}' with image '{image}'")
                dind_found = True
                
        if not dind_found:
            issues.append("❌ Docker-in-Docker: No DinD service found")
            
        # Check for secrets
        secrets = compose.get('secrets', {})
        if secrets:
            print(f"✅ Secrets: {len(secrets)} secret(s) externalized")
        else:
            issues.append("❌ Secrets: No externalized secrets found")
            
        # Check for resource limits
        resource_limits = 0
        for service_name, service in compose.get('services', {}).items():
            deploy = service.get('deploy', {})
            resources = deploy.get('resources', {})
            if resources.get('limits'):
                resource_limits += 1
                print(f"✅ Resource limits: {service_name} has resource controls")
                
        if resource_limits == 0:
            issues.append("❌ Resource limits: No resource controls found")
            
        # Check for security options
        security_opts = 0
        for service_name, service in compose.get('services', {}).items():
            if service.get('security_opt'):
                security_opts += 1
                print(f"✅ Security options: {service_name} has security controls")
                
        print("\n" + "=" * 50)
        if issues:
            print("❌ Security Issues Found:")
            for issue in issues:
                print(f"  {issue}")
            sys.exit(1)
        else:
            print("🎉 All security checks passed!")
            print("✅ Secure configuration ready for production")
            
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_secure_compose()
