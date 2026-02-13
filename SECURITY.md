# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of this project seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by emailing the repository owner. You can find contact information in the repository settings or commit history.

### What to Include

When reporting a vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Impact**: What could an attacker achieve by exploiting this vulnerability
- **Reproduction Steps**: Detailed steps to reproduce the issue
- **Affected Components**: Which parts of the codebase are affected
- **Suggested Fix**: If you have ideas on how to fix it (optional)
- **Proof of Concept**: Example code or screenshots (if applicable)

### Response Timeline

- **Initial Response**: Within 48 hours acknowledging receipt of your report
- **Status Update**: Within 5 business days with our assessment and expected timeline
- **Resolution**: We aim to release security patches within 30 days for critical vulnerabilities

### Responsible Disclosure

We kindly ask that you:

- Give us reasonable time to fix the vulnerability before public disclosure
- Make a good faith effort to avoid privacy violations, data destruction, and service interruption
- Do not exploit the vulnerability beyond what is necessary to demonstrate the issue

### Security Best Practices

When deploying this application:

1. **Never commit credentials** - Use environment variables or Azure Key Vault
2. **Rotate API keys regularly** - Change Azure service keys quarterly
3. **Use Azure RBAC** - Follow principle of least privilege
4. **Enable monitoring** - Use Application Insights to detect anomalies
5. **Implement rate limiting** - Protect against API abuse
6. **Use HTTPS only** - Enable SSL/TLS for all endpoints
7. **Validate all inputs** - Enforce maximum text length and sanitize user input
8. **Keep dependencies updated** - Regularly update Python packages
9. **Use Azure Managed Identities** - Avoid hardcoding credentials where possible
10. **Review .gitignore** - Ensure `.env` files are never committed

### Known Security Considerations

- **API Keys**: Azure Translator and OpenAI keys must be kept secure
- **Text Input**: Maximum input length should be enforced (10,000 characters recommended)
- **Rate Limiting**: No built-in rate limiting; implement at Azure App Service or API Management level
- **CORS**: Configure appropriately for your domain (currently allows all origins in development)
- **Glossary Files**: May contain proprietary terminology; keep access restricted

### Security Updates

Security updates will be released as:

- **Patch releases** (x.x.X) for non-breaking security fixes
- **Minor releases** (x.X.x) for security fixes requiring configuration changes
- **GitHub Security Advisories** for critical vulnerabilities

### Acknowledgments

We appreciate the security research community's efforts in responsibly disclosing vulnerabilities. Contributors who report valid security issues will be acknowledged in the release notes (unless they prefer to remain anonymous).

---

**Last Updated**: February 2026  
**Contact**: See repository owner contact information
