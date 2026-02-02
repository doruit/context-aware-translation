#!/usr/bin/env python3
"""
Azure Translation Service - Environment Setup (Python Alternative)
A cross-platform Python script for automating environment configuration.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict
import argparse


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")


def run_command(cmd: list, check: bool = True) -> Tuple[int, str, str]:
    """Execute a shell command and return result"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout.strip(), e.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def check_command(cmd: str) -> bool:
    """Check if a command is available in PATH"""
    code, _, _ = run_command(['which', cmd], check=False)
    return code == 0


def check_prerequisites() -> bool:
    """Check if required tools are installed"""
    print_header("Checking Prerequisites")
    
    required = {
        'az': 'Azure CLI (https://learn.microsoft.com/cli/azure/install-azure-cli)',
        'jq': 'jq - JSON processor',
        'git': 'Git (https://git-scm.com)',
    }
    
    all_present = True
    for cmd, description in required.items():
        if check_command(cmd):
            print_success(f"{cmd} found")
        else:
            print_error(f"{cmd} not found: {description}")
            all_present = False
    
    # Check Azure login
    code, _, _ = run_command(['az', 'account', 'show'], check=False)
    if code == 0:
        print_success("Azure login verified")
    else:
        print_error("Not logged into Azure. Run: az login")
        all_present = False
    
    return all_present


def get_azure_info() -> Dict[str, str]:
    """Retrieve Azure subscription information"""
    print_header("Retrieving Azure Account Information")
    
    # Get subscription ID
    code, subscription_id, _ = run_command([
        'az', 'account', 'show',
        '--query', 'id',
        '-o', 'tsv'
    ])
    
    if code != 0:
        print_error("Could not retrieve subscription ID")
        sys.exit(1)
    
    # Get tenant ID
    code, tenant_id, _ = run_command([
        'az', 'account', 'show',
        '--query', 'tenantId',
        '-o', 'tsv'
    ])
    
    # Get account name
    code, account_name, _ = run_command([
        'az', 'account', 'show',
        '--query', 'name',
        '-o', 'tsv'
    ])
    
    print_success(f"Subscription: {account_name}")
    print_info(f"Subscription ID: {subscription_id}")
    print_info(f"Tenant ID: {tenant_id}")
    
    return {
        'subscription_id': subscription_id,
        'tenant_id': tenant_id,
        'account_name': account_name
    }


def setup_azure_ad_app(app_name: str = "GitHub-azure-translation-service") -> str:
    """Create or retrieve Azure AD application for OIDC"""
    print_header("Setting Up Azure AD Application for OIDC")
    
    # Check if app exists
    print_info("Checking for existing application...")
    code, client_id, _ = run_command([
        'az', 'ad', 'app', 'list',
        '--display-name', app_name,
        '--query', '[0].appId',
        '-o', 'tsv'
    ], check=False)
    
    if code != 0 or not client_id:
        # Create new app
        print_info("Creating new Azure AD application...")
        code, client_id, _ = run_command([
            'az', 'ad', 'app', 'create',
            '--display-name', app_name,
            '--query', 'appId',
            '-o', 'tsv'
        ])
        
        if code != 0:
            print_error("Could not create Azure AD application")
            sys.exit(1)
        
        print_success(f"Created Azure AD app: {client_id}")
    else:
        print_info(f"Using existing app: {client_id}")
    
    # Create Service Principal
    print_info("Creating Service Principal...")
    run_command(['az', 'ad', 'sp', 'create', '--id', client_id], check=False)
    
    # Get Service Principal Object ID
    code, sp_object_id, _ = run_command([
        'az', 'ad', 'sp', 'show',
        '--id', client_id,
        '--query', 'id',
        '-o', 'tsv'
    ])
    
    return client_id, sp_object_id


def setup_role_assignment(
    sp_object_id: str,
    subscription_id: str
) -> bool:
    """Assign Contributor role to Service Principal"""
    print_info("Assigning Contributor role...")
    
    code, _, _ = run_command([
        'az', 'role', 'assignment', 'create',
        '--role', 'Contributor',
        '--subscription', subscription_id,
        '--assignee-object-id', sp_object_id,
        '--assignee-principal-type', 'ServicePrincipal'
    ], check=False)
    
    if code == 0:
        print_success("Contributor role assigned")
        return True
    else:
        print_warning("Role assignment may already exist")
        return False


def setup_oidc_credentials(
    client_id: str,
    repo_owner: str = "doruit",
    repo_name: str = "azure-translation-service"
) -> bool:
    """Configure GitHub OIDC federated credentials"""
    print_header("Configuring GitHub OIDC Federated Credentials")
    
    # Get existing credentials
    print_info("Retrieving existing credentials...")
    code, existing_output, _ = run_command([
        'az', 'ad', 'app', 'federated-credential', 'list',
        '--id', client_id,
        '--query', '[].name',
        '-o', 'tsv'
    ], check=False)
    
    existing = set(existing_output.split('\n')) if existing_output else set()
    
    success = True
    
    # Setup environment credentials
    for env in ['dev', 'staging', 'prod']:
        cred_name = f"GitHub-{env}"
        
        if cred_name in existing:
            print_info(f"Credential '{cred_name}' already exists, skipping...")
            continue
        
        print_info(f"Creating credential for environment: {env}")
        
        params = {
            "name": cred_name,
            "issuer": "https://token.actions.githubusercontent.com",
            "subject": f"repo:{repo_owner}/{repo_name}:environment:{env}",
            "audiences": ["api://AzureADTokenExchange"]
        }
        
        code, _, _ = run_command([
            'az', 'ad', 'app', 'federated-credential', 'create',
            '--id', client_id,
            '--parameters', json.dumps(params)
        ], check=False)
        
        if code == 0:
            print_success(f"Created: {cred_name}")
        else:
            print_warning(f"Could not create: {cred_name}")
            success = False
    
    # Setup branch credentials
    for branch in ['main', 'develop']:
        cred_name = f"GitHub-{branch}"
        
        if cred_name in existing:
            print_info(f"Credential '{cred_name}' already exists, skipping...")
            continue
        
        print_info(f"Creating credential for branch: {branch}")
        
        params = {
            "name": cred_name,
            "issuer": "https://token.actions.githubusercontent.com",
            "subject": f"repo:{repo_owner}/{repo_name}:ref:refs/heads/{branch}",
            "audiences": ["api://AzureADTokenExchange"]
        }
        
        code, _, _ = run_command([
            'az', 'ad', 'app', 'federated-credential', 'create',
            '--id', client_id,
            '--parameters', json.dumps(params)
        ], check=False)
        
        if code == 0:
            print_success(f"Created: {cred_name}")
        else:
            print_warning(f"Could not create: {cred_name}")
            success = False
    
    return success


def create_env_file(env_file: Path) -> bool:
    """Create or update .env file"""
    print_header("Creating Local Environment File")
    
    if env_file.exists():
        print_warning(".env file already exists, skipping creation")
        return False
    
    # Read template
    template_file = env_file.parent / '.env.example'
    if not template_file.exists():
        print_error(f"Template file not found: {template_file}")
        return False
    
    with open(template_file, 'r') as f:
        env_content = f.read()
    
    # Prompt for values
    print_info("Enter Azure Translator information:")
    translator_key = input("  Translator API Key: ").strip()
    translator_region = input("  Translator Region [westeurope]: ").strip() or "westeurope"
    target_language = input("  Target Language [nl]: ").strip() or "nl"
    
    print_info("Enter Post-Editor Configuration (optional):")
    enable_post_editor = input("  Enable Post-Editor? [y/N]: ").strip().lower() in ['y', 'yes']
    
    openai_endpoint = ""
    openai_key = ""
    if enable_post_editor:
        openai_endpoint = input("  Azure OpenAI Endpoint: ").strip()
        openai_key = input("  Azure OpenAI Key: ").strip()
    
    # Update template
    env_content = env_content.replace(
        "AZURE_TRANSLATOR_KEY=your_translator_key_here",
        f"AZURE_TRANSLATOR_KEY={translator_key}"
    )
    env_content = env_content.replace(
        "AZURE_TRANSLATOR_REGION=westeurope",
        f"AZURE_TRANSLATOR_REGION={translator_region}"
    )
    env_content = env_content.replace(
        "TARGET_LANGUAGE=nl",
        f"TARGET_LANGUAGE={target_language}"
    )
    env_content = env_content.replace(
        "ENABLE_POST_EDITOR=false",
        f"ENABLE_POST_EDITOR={'true' if enable_post_editor else 'false'}"
    )
    
    if openai_endpoint:
        env_content = env_content.replace(
            "AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/",
            f"AZURE_OPENAI_ENDPOINT={openai_endpoint}"
        )
    
    if openai_key:
        env_content = env_content.replace(
            "AZURE_OPENAI_KEY=your_openai_key_here",
            f"AZURE_OPENAI_KEY={openai_key}"
        )
    
    # Write file
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print_success("Created .env file")
    return True


def setup_github_secrets(
    client_id: str,
    tenant_id: str,
    subscription_id: str
) -> bool:
    """Setup GitHub repository secrets"""
    print_header("Setting Up GitHub Repository Secrets")
    
    # Check if GitHub CLI is available
    if not check_command('gh'):
        print_warning("GitHub CLI (gh) not found. Manually add these secrets:")
        print_info("Repository Settings → Secrets and variables → Actions")
        print(f"  AZURE_CLIENT_ID={client_id}")
        print(f"  AZURE_TENANT_ID={tenant_id}")
        print(f"  AZURE_SUBSCRIPTION_ID={subscription_id}")
        return False
    
    # Check if in git repository
    code, _, _ = run_command(['git', 'remote', 'get-url', 'origin'], check=False)
    if code != 0:
        print_warning("Not in a git repository. Skipping GitHub secrets setup.")
        return False
    
    print_info("Adding secrets to GitHub repository...")
    
    secrets = {
        'AZURE_CLIENT_ID': client_id,
        'AZURE_TENANT_ID': tenant_id,
        'AZURE_SUBSCRIPTION_ID': subscription_id,
    }
    
    for key, value in secrets.items():
        code, _, _ = run_command(
            ['gh', 'secret', 'set', key, '--body', value],
            check=False
        )
        
        if code == 0:
            print_success(f"{key} set")
        else:
            print_warning(f"Could not set {key}")
    
    return True


def generate_report(
    project_root: Path,
    config: Dict
) -> None:
    """Generate setup report"""
    print_header("Configuration Summary")
    
    report_file = project_root / 'SETUP_REPORT.md'
    
    report = f"""# Environment Setup Report

Generated: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}

## Azure Account Information

- **Subscription ID:** {config['subscription_id']}
- **Tenant ID:** {config['tenant_id']}
- **Subscription Name:** {config['account_name']}

## Azure AD Application

- **Application Name:** GitHub-azure-translation-service
- **Client ID:** {config['client_id']}
- **Service Principal Object ID:** {config['sp_object_id']}

## OIDC Federated Credentials

Configured for:
- **Environments:** dev, staging, prod
- **Branches:** main, develop

## Local Development

- **.env file:** {config['env_file']}
- **Status:** {'✓ Created' if Path(config['env_file']).exists() else '✗ Not created'}

## GitHub Configuration

- **Repository:** https://github.com/doruit/azure-translation-service
- **Secrets:** AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID
- **Environments:** dev, staging, prod

## Next Steps

1. If you haven't already, create the GitHub repository:
   ```bash
   gh repo create doruit/azure-translation-service --public
   git push -u origin main
   ```

2. Deploy infrastructure:
   ```bash
   ./infra/deploy.sh dev rg-translation-dev westeurope
   ```

3. Configure Azure resources (Custom Translator, OpenAI models, etc.)

4. Upload glossary to storage account

5. Deploy application via GitHub Actions or manually

## Support

For detailed deployment instructions, see:
- DEPLOYMENT.md - Complete deployment guide
- infra/README.md - Infrastructure documentation
- GITHUB_SETUP.md - GitHub repository setup guide
"""
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print_success(f"Configuration report saved to SETUP_REPORT.md")
    print("\n" + report)


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Azure Translation Service - Environment Setup"
    )
    parser.add_argument(
        '--skip-prerequisites',
        action='store_true',
        help='Skip prerequisite checks'
    )
    parser.add_argument(
        '--skip-env-file',
        action='store_true',
        help='Skip .env file creation'
    )
    parser.add_argument(
        '--skip-github',
        action='store_true',
        help='Skip GitHub configuration'
    )
    
    args = parser.parse_args()
    
    print_header("Azure Translation Service - Environment Setup")
    
    # Check prerequisites
    if not args.skip_prerequisites and not check_prerequisites():
        print_error("Prerequisites not met. Please install required tools.")
        sys.exit(1)
    
    # Get Azure info
    print()
    azure_config = get_azure_info()
    
    # Setup Azure AD App
    print()
    client_id, sp_object_id = setup_azure_ad_app()
    
    # Setup role assignment
    print()
    setup_role_assignment(sp_object_id, azure_config['subscription_id'])
    
    # Setup OIDC
    print()
    setup_oidc_credentials(client_id)
    
    # Create .env file
    if not args.skip_env_file:
        print()
        project_root = Path(__file__).parent
        env_file = project_root / '.env'
        create_env_file(env_file)
    
    # Setup GitHub
    if not args.skip_github:
        print()
        setup_github_secrets(
            client_id,
            azure_config['tenant_id'],
            azure_config['subscription_id']
        )
    
    # Generate report
    print()
    config = {
        **azure_config,
        'client_id': client_id,
        'sp_object_id': sp_object_id,
        'env_file': str(Path(__file__).parent / '.env')
    }
    generate_report(Path(__file__).parent, config)
    
    print()
    print_success("Setup completed successfully!")


if __name__ == '__main__':
    main()
