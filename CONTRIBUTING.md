# Contributing to renpy-cloud

Thank you for your interest in contributing to renpy-cloud! This document provides guidelines and instructions for contributing.

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/renpy-cloud.git
cd renpy-cloud
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode along with all development dependencies.

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=renpy_cloud --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # On Windows: start htmlcov\index.html
```

### Run Specific Tests

```bash
# Run a specific test file
pytest tests/test_config.py

# Run a specific test function
pytest tests/test_config.py::test_config_initialization

# Run tests matching a pattern
pytest -k "test_auth"
```

## Code Style

### Formatting

We use [Black](https://black.readthedocs.io/) for code formatting:

```bash
black renpy_cloud tests
```

### Linting

We use [Flake8](https://flake8.pycqa.org/) for linting:

```bash
flake8 renpy_cloud tests
```

### Type Checking

We use [mypy](http://mypy-lang.org/) for type checking:

```bash
mypy renpy_cloud
```

## Project Structure

```
renpy-cloud/
├── renpy_cloud/          # Main package
│   ├── __init__.py       # Package interface
│   ├── auth.py           # Authentication module
│   ├── client.py         # Main client interface
│   ├── config.py         # Configuration management
│   ├── api_client.py     # API communication
│   ├── file_manager.py   # File operations
│   ├── sync_manager.py   # Sync orchestration
│   └── exceptions.py     # Custom exceptions
├── infra/                # AWS infrastructure
│   ├── serverless.yml    # Serverless config
│   └── handlers/         # Lambda handlers
├── example_game/         # Example Ren'Py game
├── tests/                # Test suite
├── setup.py              # Package setup
└── README.md             # Documentation
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write clear, concise code
- Follow existing code style
- Add docstrings to functions and classes
- Update tests as needed

### 3. Write Tests

- Add tests for new features
- Ensure existing tests pass
- Aim for >90% code coverage

### 4. Update Documentation

- Update README.md if needed
- Add docstrings to new functions/classes
- Update example code if applicable

### 5. Commit Your Changes

```bash
git add .
git commit -m "Brief description of changes"
```

Use clear, descriptive commit messages:
- ✅ "Add retry logic to file upload"
- ✅ "Fix race condition in sync manager"
- ❌ "Fix stuff"
- ❌ "WIP"

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Pull Request Guidelines

### PR Checklist

- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Code follows project style (Black, Flake8)
- [ ] Documentation updated
- [ ] No unnecessary dependencies added
- [ ] Commit messages are clear

### PR Description

Include in your PR description:
- What changes were made
- Why the changes were made
- How to test the changes
- Any breaking changes
- Related issues (if any)

## Testing Guidelines

### Writing Tests

- Use descriptive test names: `test_sync_manager_handles_conflict`
- Use fixtures for common setup
- Mock external dependencies (AWS, network calls)
- Test both success and failure cases
- Test edge cases

### Example Test

```python
def test_file_manager_handles_missing_file():
    """Test that file manager raises StorageError for missing files."""
    fm = FileManager('/tmp/test')
    
    with pytest.raises(StorageError, match="Failed to read"):
        fm.read_file('/nonexistent/file.txt')
```

## Backend Development

### Testing Lambda Functions

```bash
cd infra
python -m pytest ../tests/test_lambda_handlers.py
```

### Local Testing

You can use [AWS SAM](https://aws.amazon.com/serverless/sam/) or [Serverless Offline](https://github.com/dherault/serverless-offline) for local testing.

### Deploying Changes

```bash
cd infra
serverless deploy
```

## Common Tasks

### Add a New Feature

1. Create a branch
2. Write tests first (TDD approach)
3. Implement the feature
4. Ensure tests pass
5. Update documentation
6. Submit PR

### Fix a Bug

1. Write a test that reproduces the bug
2. Fix the bug
3. Ensure test passes
4. Submit PR

### Update Dependencies

```bash
pip install --upgrade -e ".[dev]"
pip freeze > requirements.txt
```

## Questions or Problems?

- Open an issue on GitHub
- Check existing issues and PRs
- Review the README.md

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Be respectful and considerate
- Accept constructive criticism gracefully
- Focus on what's best for the project
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information

Thank you for contributing to renpy-cloud! 🎮☁️

