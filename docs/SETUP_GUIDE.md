# Environment Setup Guide

This guide explains how to use the automated environment setup scripts to configure your Azure Translation Service deployment.

## Overview

Two setup scripts are provided:

1. **setup-env.sh** - Bash script for macOS/Linux
2. **setup-env.py** - Python script (cross-platform: macOS, Linux, Windows)

Both scripts automate:
- Prerequisites checking
- Azure AD application and Service Principal creation
- OIDC federated credentials configuration
- Local `.env` file creation
- GitHub repository secrets setup
- Configuration report generation

## Prerequisites

### Required Tools

All scripts verify the following are installed:

- **Azure CLI** - [Install from Microsoft](https://learn.microsoft.com/cli/azure/install-azure-cli)
- **jq** - JSON processor (macOS: `brew install jq`, Linux: `apt-get install jq`)
- **Git** - Version control (included on most systems)
- **GitHub CLI (optional)** - For automatic secret configuration: [Install gh](https://cli.github.com/)

### Azure Subscription

- Active Azure subscription
- Sufficient permissions to:
  - Create Azure AD applications
  - Assign IAM roles
  - View subscription details

### Login to Azure

Before running either script:

```bash
az login
```

This opens a browser to authenticate with your Azure account.

## Option 1: Bash Script (macOS/Linux)

### Usage

```bash
./setup-env.sh
```

### What It Does

1. ✓ Verifies Azure CLI, jq, and Azure login
2. ✓ Retrieves your subscription and tenant information
3. ✓ Creates Azure AD application (or uses existing)
4. ✓ Creates Service Principal
5. ✓ Assigns Contributor role
6. ✓ Configures OIDC federated credentials for:
   - Environments: dev, staging, prod
   - Branches: main, develop
7. ✓ Prompts for and creates `.env` file with:
   - Azure Translator API key and configuration
   - Post-editor settings (optional)
8. ✓ Sets GitHub repository secrets (if `gh` CLI available)
9. ✓ Creates GitHub environments (dev, staging, prod)
10. ✓ Generates `SETUP_REPORT.md` with configuration summary

### Example Run

```bash
$ ./setup-env.sh

============================================
Azure Translation Service - Environment Setup
============================================

============================================
Checking Prerequisites
============================================
✓ Azure CLI found
✓ jq found
✓ Azure login verified

============================================
Retrieving Azure Account Information
============================================
✓ Subscription: My Azure Subscription
ℹ Subscription ID: 12345678-1234-1234-1234-123456789012
ℹ Tenant ID: 87654321-4321-4321-4321-210987654321

[... continues with Azure AD setup, OIDC, .env creation ...]

✓ Setup completed successfully!
```

## Option 2: Python Script (Cross-Platform)

### Usage

```bash
python3 setup-env.py
```

Or with options:

```bash
python3 setup-env.py --skip-env-file --skip-github
```

### Arguments

- `--skip-prerequisites` - Skip prerequisite checking
- `--skip-env-file` - Don't create/update `.env` file
- `--skip-github` - Skip GitHub configuration

### What It Does

Same as Bash script, but:
- Cross-platform (Windows, macOS, Linux)
- No external dependencies beyond `az`, `jq`, `git`
- Better error handling and subprocess management
- JSON parsing via Python's built-in json module

## Interactive Prompts

Both scripts prompt for information:

### Azure Translator Configuration

```
Enter Azure Translator information:
  Translator API Key: < paste your key >
  Translator Region [westeurope]: < press Enter or enter custom region >
  Target Language [nl]: < press Enter or enter different language >
```

Find your keys in Azure Portal:
1. **Cognitive Services** → Your Translator resource
2. **Keys and Endpoint** section
3. Copy "Key 1" or "Key 2"

### Post-Editor Configuration (Optional)

```
Enter Post-Editor Configuration (leave blank to skip):
  Enable Post-Editor [y/N]: y
  Azure OpenAI Endpoint: https://your-resource.openai.azure.com/
  Azure OpenAI Key: < paste your key >
```

Leave blank to skip OpenAI post-editor (recommended for initial setup).

## Generated Files

### .env File

Local environment configuration created from `.env.example` template:

```env
# Azure Translator Configuration
AZURE_TRANSLATOR_KEY=your_key_here
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=westeurope
CUSTOM_TRANSLATOR_CATEGORY=general

# Translation Configuration
TARGET_LANGUAGE=nl
GLOSSARY_PATH=data/glossary.tsv

# Post-Editor Configuration (Optional)
ENABLE_POST_EDITOR=false
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_KEY=...
AZURE_OPENAI_MODEL=gpt-4
```

**⚠️ Important:** This file contains secrets. Never commit to version control:
- Already in `.gitignore`
- Only for local development and server environment variables

### SETUP_REPORT.md

Comprehensive report showing:
- Azure subscription details
- Azure AD application credentials
- OIDC configuration
- GitHub secrets status
- Next steps and troubleshooting

Example:

```markdown
# Environment Setup Report

Generated: 2024-02-02 10:30:45

## Azure Account Information
- Subscription ID: 12345678-...
- Tenant ID: 87654321-...
- Subscription Name: My Azure Subscription

## Azure AD Application
- Application Name: GitHub-azure-translation-service
- Client ID: abcdef12-3456-7890-abcd-ef1234567890
- Service Principal Object ID: ...

## OIDC Federated Credentials
Configured for:
- Environments: dev, staging, prod
- Branches: main, develop

## Next Steps
1. Create GitHub repository...
2. Deploy infrastructure...
```

## GitHub Configuration

### Automatic Setup (with GitHub CLI)

If `gh` CLI is available, the script:

1. Creates/verifies GitHub repository secrets:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`

2. Creates GitHub environments:
   - `dev`
   - `staging`
   - `prod`

### Manual Setup (without GitHub CLI)

If `gh` is not available, the script displays values to add manually:

1. Go to your repository on GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:
   ```
   AZURE_CLIENT_ID = <value from script output>
   AZURE_TENANT_ID = <value from script output>
   AZURE_SUBSCRIPTION_ID = <value from script output>
   ```

4. Create environments (**Settings** → **Environments**):
   - Click **New environment** for each: dev, staging, prod

## Running the Application Locally

After setup:

1. **Verify .env file:**
   ```bash
   cat .env | grep -v "^#" | grep -v "^$"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run application:**
   ```bash
   python run.py
   ```
   
   Or with Uvicorn directly:
   ```bash
   uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access web UI:**
   - Open [http://localhost:8000](http://localhost:8000)
   - Or [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Deploying Infrastructure

After setup, deploy Azure resources:

### Option 1: GitHub Actions (Recommended)

1. Push code to GitHub repository
2. Go to **Actions** tab
3. Select **Deploy Infrastructure** workflow
4. Click **Run workflow**
5. Select environment and region

### Option 2: Local Bash Script

```bash
./infra/deploy.sh dev rg-translation-dev westeurope
```

Parameters:
- `dev` - Environment name (dev, staging, prod)
- `rg-translation-dev` - Resource group name
- `westeurope` - Azure region

### Option 3: Manual Azure CLI

```bash
az deployment group create \
  --resource-group rg-translation-dev \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.dev.json
```

## Troubleshooting

### "Azure CLI is not installed"

Install from: https://learn.microsoft.com/cli/azure/install-azure-cli

### "Not logged into Azure"

Run:
```bash
az login
```

### ".env file already exists"

The script preserves existing `.env` files. To recreate:

```bash
rm .env
./setup-env.sh  # or python3 setup-env.py
```

### "GitHub CLI not found"

Install from: https://cli.github.com/

Or manually add repository secrets via GitHub web interface (see Manual Setup section).

### "Could not set GitHub secret"

Make sure:
1. You're in the git repository directory
2. Remote is configured: `git remote -v`
3. GitHub CLI is authenticated: `gh auth login`

### "Service Principal may already exist"

This is expected if setup was run before. The script will use the existing principal.

### "Role assignment may already exist"

This is expected if setup was run before. The script will reuse the existing role assignment.

## Security Considerations

### .env File

- Contains sensitive credentials
- Should never be committed to version control
- Ensure proper file permissions: `chmod 600 .env`
- Use server environment variables for production

### Azure AD Application

- Client ID is non-sensitive and can be public
- Uses OIDC federated credentials (no secrets stored)
- Service Principal scoped to your subscription only
- Contributor role can be restricted to specific resource groups

### GitHub Secrets

- Only visible to GitHub Actions workflows
- Cannot be viewed after creation
- Can be rotated by deleting and recreating

## Next Steps After Setup

1. **Review configuration** - Check `SETUP_REPORT.md` for details
2. **Deploy infrastructure** - Use Bicep templates (see "Deploying Infrastructure")
3. **Configure glossary** - Update `data/glossary.tsv` with your terms
4. **Deploy application** - Push to GitHub and let CI/CD handle it
5. **Test translation** - Visit web UI and test with sample text
6. **Monitor** - Check Application Insights for metrics and logs

## Getting Help

For issues, see:

- **README.md** - Project overview and quick start
- **DEPLOYMENT.md** - Complete deployment guide
- **infra/README.md** - Infrastructure documentation
- **GITHUB_SETUP.md** - GitHub repository setup

## Running Setup Again

It's safe to run setup multiple times:

- Existing Azure AD applications are reused
- OIDC credentials are skipped if already present
- .env file is not overwritten
- GitHub secrets are updated if changed

To update only `.env`:

**Bash:**
```bash
rm .env && ./setup-env.sh
```

**Python:**
```bash
rm .env && python3 setup-env.py
```

To update only GitHub secrets:

**Bash:**
```bash
./setup-env.sh  # and skip .env creation when prompted
```

**Python:**
```bash
python3 setup-env.py --skip-env-file
```
