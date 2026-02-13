# Before Making Repository Public - Checklist

⚠️ **IMPORTANT**: Complete ALL items before making this repository public.

## 🔴 Critical (Must Complete)

- [x] **Azure Translator service removed** - No key rotation needed
- [x] **Verify `.env` not in git history** - Confirmed not tracked
- [x] **Contoso branding sanitized** - Replaced with generic examples
- [ ] **Update all `doruit` references** - Replace with `YOUR_GITHUB_USERNAME` 
- [ ] **Update all `context-aware-translation` references** - Replace with `YOUR_REPO_NAME`
- [ ] **Remove deployment artifacts** - Delete `*.zip` files from repository
- [x] **SECURITY.md created** - Security policy documented

## 🟡 High Priority (Strongly Recommended)

- [ ] **Update screenshot URL in README** - Fix or remove broken image link
- [ ] **Test glossary examples** - Verify `glossary-acme.tsv` works correctly
- [ ] **Review all documentation** - Ensure no internal references remain
- [ ] **Update LICENSE copyright** - Verify year and owner information
- [ ] **Add CONTRIBUTORS.md** - If you want to acknowledge contributors

## 🟢 Optional (Consider)

- [ ] **Add GitHub badges** - CI/CD status, license, etc.
- [ ] **Set up GitHub Dependabot** - Automated dependency updates
- [ ] **Configure GitHub security scanning** - Secret scanning, code scanning
- [ ] **Create issue templates** - Bug reports, feature requests
- [ ] **Add pull request template** - Contribution guidelines
- [ ] **Document API rate limits** - Add recommendations in README

## 📋 Files to Update (Hardcoded References)

The following files contain hardcoded `doruit` or `context-aware-translation` references:

### Documentation Files
- [ ] `README.md` - Screenshot URL
- [ ] `.github/CONTRIBUTING.md` - Clone instructions
- [ ] `docs/GITHUB_SETUP.md` - All gh commands and URLs (17 occurrences)
- [ ] `docs/DEPLOYMENT.md` - Repository creation commands (6 occurrences)
- [ ] `docs/SETUP_GUIDE.md` - Application name reference
- [ ] `docs/PROBLEM_STATEMENT_ANALYSIS.md` - Repository name
- [ ] `docs/IMPLEMENTATION_SUMMARY.md` - Repository references

### Infrastructure Files
- [ ] `infra/README.md` - GITHUB_ORG and GITHUB_REPO variables

### Scripts (Already Updated)
- [x] `setup-env.py` - Updated to use placeholders

## 🗑️ Files to Delete

Run these commands to remove deployment artifacts:

```bash
cd /Users/doruit/action-translation-dict
git rm --cached app-logs.zip deploy-clean.zip latest-logs.zip deploy.zip
rm -f app-logs.zip deploy-clean.zip latest-logs.zip deploy.zip
git commit -m "Remove deployment artifacts before public release"
```

## ✅ Final Verification Commands

Before making public, run:

```bash
# 1. Check for any .env files in history
git log --all --full-history -- .env

# 2. Search for potential secrets
git grep -i "password\|secret\|key\|token" -- ':!*.md' ':!SECURITY.md'

# 3. Search for Contoso references
git grep -i "contoso"

# 4. Search for hardcoded GitHub references
git grep -E "doruit|context-aware-translation" -- ':!BEFORE_PUBLIC_CHECKLIST.md'

# 5. Check for deployment artifacts
find . -name "*.zip" -not -path "./venv/*"

# 6. Verify .gitignore
git check-ignore -v .env data/glossary.tsv *.zip
```

## 🔒 Optional: Additional Security Tools

```bash
# Install and run gitleaks (secret scanner)
brew install gitleaks
gitleaks detect --source . --verbose

# Install and run trufflehog (secret scanner)
brew install trufflesecurity/trufflehog/trufflehog
trufflehog filesystem . --only-verified
```

## 📝 Recommended README Updates

Add to README.md:

```markdown
## ⚠️ Before You Start

This is a template repository. Before deploying:

1. Replace all instances of `YOUR_GITHUB_USERNAME` with your GitHub username
2. Replace all instances of `YOUR_REPO_NAME` with your repository name
3. Update the screenshot URL in README.md or remove it
4. Generate new Azure service keys (never use example keys)
5. Review and customize the glossary files in `data/`
```

## 🎯 Post-Public Tasks

After making the repository public:

1. **Enable GitHub Features**
   - [ ] Enable Dependabot security updates
   - [ ] Enable secret scanning
   - [ ] Enable code scanning (CodeQL)
   - [ ] Set up branch protection rules

2. **Create Initial Release**
   - [ ] Tag version 1.0.0
   - [ ] Create release notes
   - [ ] Build and publish Docker image (if applicable)

3. **Community Setup**
   - [ ] Watch for first issues/PRs
   - [ ] Respond to community feedback
   - [ ] Update documentation based on questions

---

**Completion Status**: 4/17 checklist items completed

**Ready for Public Release**: ❌ Not yet - complete critical items first
