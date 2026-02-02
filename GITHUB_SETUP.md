# Creating the GitHub Repository

Follow these steps to create the public GitHub repository under `github.com/doruit`.

## Repository Setup

### Option 1: Using GitHub CLI (Recommended)

```bash
# Navigate to the project directory
cd /Users/doruit/action-translation-dict

# Initialize git if not already done
git init

# Create GitHub repository
gh repo create doruit/azure-translation-service \
  --public \
  --description "Azure Translation Service with glossary enforcement - preserve domain-specific terminology during translation" \
  --homepage "https://github.com/doruit/azure-translation-service"

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Azure Translation Service with Glossary Enforcement

- FastAPI application with Python 3.11
- Azure Translator Text v3 integration
- TSV glossary-based terminology enforcement
- Optional Azure OpenAI post-editor
- Complete Bicep infrastructure templates
- GitHub Actions CI/CD pipeline
- Docker containerization
- Comprehensive documentation"

# Set main as default branch
git branch -M main

# Push to GitHub
git remote add origin https://github.com/doruit/azure-translation-service.git
git push -u origin main

# Create develop branch
git checkout -b develop
git push -u origin develop
```

### Option 2: Using GitHub Web Interface

1. **Go to GitHub:**
   - Visit https://github.com/new
   - Or click your profile → "Your repositories" → "New"

2. **Repository Settings:**
   - Owner: `doruit`
   - Repository name: `azure-translation-service`
   - Description: `Azure Translation Service with glossary enforcement - preserve domain-specific terminology during translation`
   - Visibility: **Public**
   - ✅ Add a README file: **No** (we already have one)
   - ✅ Add .gitignore: **No** (we already have one)
   - Choose a license: **MIT** (recommended)

3. **Create Repository**

4. **Push Local Code:**
   ```bash
   cd /Users/doruit/action-translation-dict
   git init
   git add .
   git commit -m "Initial commit: Azure Translation Service with Glossary Enforcement"
   git branch -M main
   git remote add origin https://github.com/doruit/azure-translation-service.git
   git push -u origin main
   
   # Create develop branch
   git checkout -b develop
   git push -u origin develop
   ```

## Repository Configuration

### 1. Branch Protection Rules

```bash
# Via GitHub CLI
gh api repos/doruit/azure-translation-service/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

Or via web interface:
- Go to Settings → Branches → Add rule
- Branch name pattern: `main`
- ✅ Require pull request reviews before merging (1 approval)
- ✅ Require status checks to pass before merging
  - Select: `test`, `build`
- ✅ Require branches to be up to date before merging

### 2. Enable GitHub Actions

- Go to Settings → Actions → General
- Actions permissions: **Allow all actions and reusable workflows**
- Workflow permissions: **Read and write permissions**
- ✅ Allow GitHub Actions to create and approve pull requests

### 3. Configure Environments

Create three environments: `dev`, `staging`, `prod`

```bash
# Via GitHub CLI
for ENV in dev staging prod; do
  gh api repos/doruit/azure-translation-service/environments/$ENV \
    --method PUT
done

# Add protection rules for prod
gh api repos/doruit/azure-translation-service/environments/prod \
  --method PUT \
  --field reviewers='[{"type":"User","id":YOUR_USER_ID}]'
```

Or via web interface:
- Go to Settings → Environments → New environment
- Create: `dev`, `staging`, `prod`
- For `prod`:
  - ✅ Required reviewers: Add yourself
  - Wait timer: 0 minutes

### 4. Add Topics/Tags

```bash
gh repo edit doruit/azure-translation-service \
  --add-topic azure \
  --add-topic translation \
  --add-topic translator \
  --add-topic glossary \
  --add-topic fastapi \
  --add-topic python \
  --add-topic azure-translator \
  --add-topic azure-openai \
  --add-topic bicep \
  --add-topic github-actions \
  --add-topic docker \
  --add-topic terminology \
  --add-topic localization
```

### 5. Add Repository Secrets (for CI/CD)

After setting up Azure AD application (see DEPLOYMENT.md):

```bash
# Add Azure credentials
gh secret set AZURE_CLIENT_ID --body "your-client-id"
gh secret set AZURE_TENANT_ID --body "your-tenant-id"
gh secret set AZURE_SUBSCRIPTION_ID --body "your-subscription-id"

# Add per-environment secrets
gh secret set AZURE_APP_SERVICE_NAME --env dev --body "your-app-service-name-dev"
gh secret set AZURE_APP_SERVICE_NAME --env prod --body "your-app-service-name-prod"
```

### 6. Enable GitHub Pages (Optional)

If you want to host documentation:
- Go to Settings → Pages
- Source: Deploy from a branch
- Branch: `main` / `docs` folder
- Save

### 7. Configure Repository Settings

- Go to Settings → General
- Features:
  - ✅ Wikis (for additional documentation)
  - ✅ Issues (for bug tracking)
  - ✅ Projects (for project management)
  - ✅ Discussions (for community Q&A)
- Pull Requests:
  - ✅ Allow squash merging
  - ✅ Automatically delete head branches

## Repository Description

Update the repository with a comprehensive description:

**Short Description:**
```
Azure Translation Service with glossary enforcement - preserve domain-specific terminology during translation
```

**About/Details:**
```
🌐 Production-ready translation service using Azure Translator with deterministic glossary enforcement

Features:
✅ Azure Translator Text v3 with Custom Translator support
✅ TSV-based glossary for domain-specific terminology
✅ Optional Azure OpenAI post-editing for fluency
✅ FastAPI + Python 3.11
✅ Complete Bicep infrastructure templates
✅ GitHub Actions CI/CD pipeline
✅ Docker containerization
✅ Comprehensive test suite

Perfect for IT service management, healthcare, legal, or any domain requiring terminology consistency during translation.
```

## Repository Structure

After pushing, your repository will have:

```
azure-translation-service/
├── .github/
│   └── workflows/
│       ├── ci-cd.yml
│       └── deploy-infrastructure.yml
├── data/
│   └── glossary.tsv
├── infra/
│   ├── main.bicep
│   ├── main.parameters.dev.json
│   ├── main.parameters.prod.json
│   ├── deploy.sh
│   └── README.md
├── src/
│   ├── config/
│   ├── routes/
│   ├── services/
│   ├── terminology/
│   ├── ui/
│   └── app.py
├── tests/
│   ├── conftest.py
│   └── test_enforcer.py
├── .env.example
├── .gitignore
├── DEPLOYMENT.md
├── Dockerfile
├── docker-compose.yml
├── README.md
├── requirements.txt
└── run.py
```

## Initial README Badges

Add these badges to the top of README.md:

```markdown
# Azure Translation Service with Glossary Enforcement

[![CI/CD](https://github.com/doruit/azure-translation-service/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/doruit/azure-translation-service/actions/workflows/ci-cd.yml)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Azure](https://img.shields.io/badge/Azure-Translator-0078D4?logo=microsoft-azure)](https://azure.microsoft.com/en-us/services/cognitive-services/translator/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://hub.docker.com/)
```

## Post-Creation Checklist

- [ ] Repository created and pushed
- [ ] Branch protection enabled for `main`
- [ ] Environments configured (dev, staging, prod)
- [ ] Topics/tags added
- [ ] License file added (MIT recommended)
- [ ] CODEOWNERS file created (optional)
- [ ] Issue templates created (optional)
- [ ] Security policy added (SECURITY.md)
- [ ] Contributing guidelines (CONTRIBUTING.md)
- [ ] Azure AD application configured
- [ ] GitHub secrets added
- [ ] First workflow run successful

## Security Considerations

1. **Never commit secrets:**
   - `.env` is in `.gitignore`
   - Use GitHub secrets for credentials
   - Use Azure Key Vault for production

2. **Dependabot:**
   - Enable Dependabot alerts
   - Enable Dependabot security updates
   - Configure dependabot.yml for automated updates

3. **Code Scanning:**
   - Enable CodeQL analysis
   - Configure security scanning in workflows

## Next Steps

1. Complete Azure infrastructure deployment (see DEPLOYMENT.md)
2. Configure Custom Translator (optional)
3. Deploy application via GitHub Actions
4. Set up monitoring and alerts
5. Invite collaborators
6. Create first release

## Repository URLs

After creation, your repository will be accessible at:

- **Repository:** https://github.com/doruit/azure-translation-service
- **Issues:** https://github.com/doruit/azure-translation-service/issues
- **Actions:** https://github.com/doruit/azure-translation-service/actions
- **Releases:** https://github.com/doruit/azure-translation-service/releases
- **Container Registry:** ghcr.io/doruit/azure-translation-service
