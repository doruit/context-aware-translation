# Contributing to Azure Translation Service

Thank you for your interest in contributing! This project welcomes contributions and suggestions.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/action-translation-dict.git
   cd action-translation-dict
   ```

2. **Create a virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest black ruff  # Development tools
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure credentials
   ```

## Code Quality Standards

### Linting and Formatting

Before committing, ensure your code passes all quality checks:

```bash
# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Run type checks (if using mypy)
mypy src/
```

### Testing

All new features must include tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_enforcer.py -v
```

**Coverage Requirements:**
- Minimum 80% code coverage for new code
- All critical paths must be tested
- Edge cases should be covered

## Contribution Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following existing patterns
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   black src/ tests/
   ruff check src/ tests/
   pytest --cov=src
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   **Commit Message Convention:**
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test additions/changes
   - `refactor:` Code refactoring
   - `chore:` Maintenance tasks

5. **Push and create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Guidelines

- **Title**: Clear, descriptive title following commit convention
- **Description**: Explain what changed and why
- **Tests**: Include test results or screenshots
- **Documentation**: Update relevant docs if needed
- **Breaking Changes**: Clearly mark any breaking changes

## Code Style

- **Python**: Follow PEP 8 guidelines
- **Line length**: 88 characters (Black default)
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Google-style docstrings for public functions

Example:
```python
def enforce_terms(text: str, glossary: List[GlossaryEntry]) -> EnforcedResult:
    """Enforce glossary terms in the given text.
    
    Args:
        text: The text to process
        glossary: List of glossary entries to enforce
        
    Returns:
        EnforcedResult containing modified text and applied terms
        
    Raises:
        ValueError: If glossary is empty
    """
    pass
```

## Areas for Contribution

### High-Priority
- Performance optimizations for large glossaries
- Support for additional language pairs
- Caching mechanisms for translations
- Rate limiting improvements

### Medium-Priority
- UI/UX enhancements
- Additional test coverage
- Documentation improvements
- Example integrations (ServiceNow, Salesforce, etc.)

### Good First Issues
- Look for issues labeled `good-first-issue`
- Documentation updates
- Test additions
- Bug fixes

## Questions?

- **Issues**: Open an issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Security**: Report security issues privately (see SECURITY.md)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
