#!/bin/bash
set -e

# ============================================================================
# Azure Translation Service - Environment Setup Automation
# ============================================================================
# This script automates the setup of environment variables for:
# 1. Local development (.env file)
# 2. GitHub repository secrets
# 3. Azure App Service configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"
ENV_FILE="$PROJECT_ROOT/.env"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed"
        return 1
    fi
    return 0
}

# ============================================================================
# Prerequisites Check
# ============================================================================

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing=0
    
    if ! check_command az; then
        print_error "Azure CLI is required. Install from: https://learn.microsoft.com/cli/azure/install-azure-cli"
        missing=1
    else
        print_success "Azure CLI found"
    fi
    
    if ! check_command jq; then
        print_error "jq is required for JSON parsing"
        print_info "Install: brew install jq (macOS) or apt-get install jq (Linux)"
        missing=1
    else
        print_success "jq found"
    fi
    
    if ! az account show &> /dev/null; then
        print_error "Not logged into Azure. Run: az login"
        missing=1
    else
        print_success "Azure login verified"
    fi
    
    if [ $missing -eq 1 ]; then
        return 1
    fi
    
    return 0
}

# ============================================================================
# Get Azure Subscription Info
# ============================================================================

get_azure_info() {
    print_header "Retrieving Azure Account Information"
    
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    TENANT_ID=$(az account show --query tenantId -o tsv)
    ACCOUNT_NAME=$(az account show --query name -o tsv)
    
    print_success "Subscription: $ACCOUNT_NAME"
    print_info "Subscription ID: $SUBSCRIPTION_ID"
    print_info "Tenant ID: $TENANT_ID"
}

# ============================================================================
# Create/Update Azure AD Service Principal with OIDC
# ============================================================================

setup_azure_ad_app() {
    print_header "Setting Up Azure AD Application for OIDC"
    
    local app_name="GitHub-azure-translation-service"
    
    # Check if app already exists
    print_info "Checking for existing application..."
    local existing_app=$(az ad app list --display-name "$app_name" --query "[0].appId" -o tsv 2>/dev/null || echo "")
    
    if [ -z "$existing_app" ]; then
        print_info "Creating new Azure AD application..."
        CLIENT_ID=$(az ad app create --display-name "$app_name" --query appId -o tsv)
        print_success "Created Azure AD app: $CLIENT_ID"
    else
        CLIENT_ID="$existing_app"
        print_info "Using existing app: $CLIENT_ID"
    fi
    
    # Create Service Principal
    print_info "Creating Service Principal..."
    az ad sp create --id "$CLIENT_ID" > /dev/null 2>&1 || print_warning "Service Principal may already exist"
    
    # Get Service Principal Object ID
    SP_OBJECT_ID=$(az ad sp show --id "$CLIENT_ID" --query id -o tsv)
    
    # Assign Contributor role
    print_info "Assigning Contributor role..."
    az role assignment create \
        --role Contributor \
        --subscription "$SUBSCRIPTION_ID" \
        --assignee-object-id "$SP_OBJECT_ID" \
        --assignee-principal-type ServicePrincipal > /dev/null 2>&1 || print_warning "Role assignment may already exist"
    
    print_success "Contributor role assigned"
}

# ============================================================================
# Configure OIDC Federated Credentials
# ============================================================================

setup_oidc_credentials() {
    print_header "Configuring GitHub OIDC Federated Credentials"
    
    local repo_owner="doruit"
    local repo_name="azure-translation-service"
    
    # Get existing credentials
    print_info "Retrieving existing credentials..."
    local existing=$(az ad app federated-credential list --id "$CLIENT_ID" --query "[].name" -o tsv 2>/dev/null || echo "")
    
    # Environments
    for env in dev staging prod; do
        local cred_name="GitHub-$env"
        if echo "$existing" | grep -q "$cred_name"; then
            print_info "Credential '$cred_name' already exists, skipping..."
        else
            print_info "Creating credential for environment: $env"
            az ad app federated-credential create \
                --id "$CLIENT_ID" \
                --parameters "{
                    \"name\": \"$cred_name\",
                    \"issuer\": \"https://token.actions.githubusercontent.com\",
                    \"subject\": \"repo:$repo_owner/$repo_name:environment:$env\",
                    \"audiences\": [\"api://AzureADTokenExchange\"]
                }" > /dev/null 2>&1
            print_success "Created: $cred_name"
        fi
    done
    
    # Branches
    for branch in main develop; do
        local cred_name="GitHub-$branch"
        if echo "$existing" | grep -q "$cred_name"; then
            print_info "Credential '$cred_name' already exists, skipping..."
        else
            print_info "Creating credential for branch: $branch"
            az ad app federated-credential create \
                --id "$CLIENT_ID" \
                --parameters "{
                    \"name\": \"$cred_name\",
                    \"issuer\": \"https://token.actions.githubusercontent.com\",
                    \"subject\": \"repo:$repo_owner/$repo_name:ref:refs/heads/$branch\",
                    \"audiences\": [\"api://AzureADTokenExchange\"]
                }" > /dev/null 2>&1
            print_success "Created: $cred_name"
        fi
    done
}

# ============================================================================
# Create or Update .env File
# ============================================================================

create_env_file() {
    print_header "Creating Local Environment File"
    
    local translator_key=""
    local translator_endpoint="https://api.cognitive.microsofttranslator.com"
    local translator_region="${AZURE_REGION:-westeurope}"
    local target_language="${TARGET_LANGUAGE:-nl}"
    
    # Prompt for values if creating new file
    if [ ! -f "$ENV_FILE" ]; then
        echo
        print_info "Enter Azure Translator information:"
        read -p "  Translator API Key: " translator_key
        read -p "  Translator Region [$translator_region]: " translator_region_input
        [ -n "$translator_region_input" ] && translator_region="$translator_region_input"
        
        read -p "  Target Language [$target_language]: " target_language_input
        [ -n "$target_language_input" ] && target_language="$target_language_input"
        
        print_info "Enter Post-Editor Configuration (leave blank to skip):"
        read -p "  Enable Post-Editor [y/N]: " enable_post_editor
        enable_post_editor="${enable_post_editor:-N}"
        
        local openai_endpoint=""
        local openai_key=""
        if [[ "$enable_post_editor" == "y" || "$enable_post_editor" == "Y" ]]; then
            read -p "  Azure OpenAI Endpoint: " openai_endpoint
            read -p "  Azure OpenAI Key: " openai_key
        fi
        
        # Create .env from template
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        
        # Update values
        sed -i.bak "s|AZURE_TRANSLATOR_KEY=.*|AZURE_TRANSLATOR_KEY=$translator_key|" "$ENV_FILE"
        sed -i.bak "s|AZURE_TRANSLATOR_ENDPOINT=.*|AZURE_TRANSLATOR_ENDPOINT=$translator_endpoint|" "$ENV_FILE"
        sed -i.bak "s|AZURE_TRANSLATOR_REGION=.*|AZURE_TRANSLATOR_REGION=$translator_region|" "$ENV_FILE"
        sed -i.bak "s|TARGET_LANGUAGE=.*|TARGET_LANGUAGE=$target_language|" "$ENV_FILE"
        sed -i.bak "s|ENABLE_POST_EDITOR=.*|ENABLE_POST_EDITOR=$([ "$enable_post_editor" = "y" ] && echo "true" || echo "false")|" "$ENV_FILE"
        
        if [ -n "$openai_endpoint" ]; then
            sed -i.bak "s|AZURE_OPENAI_ENDPOINT=.*|AZURE_OPENAI_ENDPOINT=$openai_endpoint|" "$ENV_FILE"
        fi
        if [ -n "$openai_key" ]; then
            sed -i.bak "s|AZURE_OPENAI_KEY=.*|AZURE_OPENAI_KEY=$openai_key|" "$ENV_FILE"
        fi
        
        rm -f "$ENV_FILE.bak"
        print_success "Created .env file"
    else
        print_warning ".env file already exists, skipping creation"
    fi
}

# ============================================================================
# Setup GitHub Secrets
# ============================================================================

setup_github_secrets() {
    print_header "Setting Up GitHub Repository Secrets"
    
    # Check if GitHub CLI is available
    if ! check_command gh; then
        print_warning "GitHub CLI (gh) not found. You'll need to manually add these secrets:"
        print_info "Repository Settings → Secrets and variables → Actions"
        echo
        echo "  AZURE_CLIENT_ID=$CLIENT_ID"
        echo "  AZURE_TENANT_ID=$TENANT_ID"
        echo "  AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID"
        return 0
    fi
    
    # Check if we're in a GitHub repository
    if ! git remote get-url origin &> /dev/null; then
        print_warning "Not in a git repository. Skipping GitHub secrets setup."
        return 0
    fi
    
    print_info "Adding secrets to GitHub repository..."
    
    gh secret set AZURE_CLIENT_ID --body "$CLIENT_ID" 2>/dev/null && \
        print_success "AZURE_CLIENT_ID set" || \
        print_warning "Could not set AZURE_CLIENT_ID"
    
    gh secret set AZURE_TENANT_ID --body "$TENANT_ID" 2>/dev/null && \
        print_success "AZURE_TENANT_ID set" || \
        print_warning "Could not set AZURE_TENANT_ID"
    
    gh secret set AZURE_SUBSCRIPTION_ID --body "$SUBSCRIPTION_ID" 2>/dev/null && \
        print_success "AZURE_SUBSCRIPTION_ID set" || \
        print_warning "Could not set AZURE_SUBSCRIPTION_ID"
}

# ============================================================================
# Setup GitHub Environments
# ============================================================================

setup_github_environments() {
    print_header "Setting Up GitHub Environments"
    
    # Check if GitHub CLI is available
    if ! check_command gh; then
        print_warning "GitHub CLI (gh) not found. You'll need to manually create environments:"
        print_info "Repository Settings → Environments"
        echo "  - dev"
        echo "  - staging"
        echo "  - prod"
        return 0
    fi
    
    # Check if we're in a GitHub repository
    if ! git remote get-url origin &> /dev/null; then
        print_warning "Not in a git repository. Skipping GitHub environments setup."
        return 0
    fi
    
    print_info "Creating GitHub environments..."
    
    for env in dev staging prod; do
        gh api repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/environments/$env \
            --method PUT > /dev/null 2>&1 && \
            print_success "Environment '$env' configured" || \
            print_warning "Could not configure environment '$env'"
    done
}

# ============================================================================
# Deploy Infrastructure
# ============================================================================

deploy_infrastructure() {
    print_header "Infrastructure Deployment Options"
    
    echo
    print_info "You can now deploy infrastructure using:"
    echo
    echo "  Option 1 - GitHub Actions (Recommended):"
    echo "    Go to: https://github.com/doruit/azure-translation-service/actions"
    echo "    Workflow: Deploy Infrastructure"
    echo "    Select environment (dev/staging/prod)"
    echo
    echo "  Option 2 - Local Script:"
    echo "    ./infra/deploy.sh dev rg-translation-dev westeurope"
    echo
    echo "  Option 3 - Manual Azure CLI:"
    echo "    az deployment group create \\"
    echo "      --resource-group rg-translation-dev \\"
    echo "      --template-file infra/main.bicep \\"
    echo "      --parameters infra/main.parameters.dev.json"
    echo
}

# ============================================================================
# Generate Configuration Report
# ============================================================================

generate_report() {
    print_header "Configuration Summary"
    
    cat > "$PROJECT_ROOT/SETUP_REPORT.md" <<EOF
# Environment Setup Report

Generated: $(date)

## Azure Account Information

- **Subscription ID:** $SUBSCRIPTION_ID
- **Tenant ID:** $TENANT_ID
- **Subscription Name:** $ACCOUNT_NAME

## Azure AD Application

- **Application Name:** GitHub-azure-translation-service
- **Client ID:** $CLIENT_ID
- **Service Principal Object ID:** $SP_OBJECT_ID

## OIDC Federated Credentials

Configured for:
- **Environments:** dev, staging, prod
- **Branches:** main, develop

## Local Development

- **.env file:** $ENV_FILE
- **Status:** $([ -f "$ENV_FILE" ] && echo "✓ Created" || echo "✗ Not created")

## GitHub Configuration

- **Repository:** https://github.com/doruit/azure-translation-service
- **Secrets:** AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID
- **Environments:** dev, staging, prod

## Next Steps

1. If you haven't already, create the GitHub repository:
   \`\`\`bash
   gh repo create doruit/azure-translation-service --public
   git push -u origin main
   \`\`\`

2. Deploy infrastructure:
   \`\`\`bash
   ./infra/deploy.sh dev rg-translation-dev westeurope
   \`\`\`

3. Configure Azure resources (Custom Translator, OpenAI models, etc.)

4. Upload glossary to storage account

5. Deploy application via GitHub Actions or manually

## Support

For detailed deployment instructions, see:
- DEPLOYMENT.md - Complete deployment guide
- infra/README.md - Infrastructure documentation
- GITHUB_SETUP.md - GitHub repository setup guide

EOF
    
    print_success "Configuration report saved to SETUP_REPORT.md"
    cat "$PROJECT_ROOT/SETUP_REPORT.md"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    print_header "Azure Translation Service - Environment Setup"
    
    # Check prerequisites
    if ! check_prerequisites; then
        print_error "Prerequisites not met. Please install required tools and try again."
        exit 1
    fi
    
    echo
    
    # Get Azure info
    get_azure_info
    
    echo
    
    # Setup Azure AD App
    setup_azure_ad_app
    
    echo
    
    # Setup OIDC
    setup_oidc_credentials
    
    echo
    
    # Create .env file
    create_env_file
    
    echo
    
    # Setup GitHub secrets (if available)
    setup_github_secrets
    
    echo
    
    # Setup GitHub environments (if available)
    setup_github_environments
    
    echo
    
    # Deployment info
    deploy_infrastructure
    
    echo
    
    # Generate report
    generate_report
    
    echo
    print_success "Setup completed successfully!"
    echo
}

# Run main function
main "$@"
