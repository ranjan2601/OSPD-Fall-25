# Pull Request

## Description

Brief description of what this PR accomplishes and why it's needed.

## Type of Change

Please select the type of change this PR represents:

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Code refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test coverage improvement
- [ ] 🔨 Build/CI configuration changes

## Related Issues

Closes #(issue_number) 
Relates to #(issue_number)

## Changes Made

### Components Modified
- [ ] `message` - Message protocol
- [ ] `mail_client_api` - Mail client protocol  
- [ ] `gmail_message_impl` - Gmail message implementation
- [ ] `gmail_client_impl` - Gmail client implementation
- [ ] Root configuration (pyproject.toml, CI/CD, etc.)
- [ ] Documentation
- [ ] Tests

### Detailed Changes
- 
- 
- 

## Testing

### Test Categories Covered
- [ ] Unit tests (`src/*/tests/`)
- [ ] Integration tests (`tests/integration/`)
- [ ] End-to-end tests (`tests/e2e/`)
- [ ] CircleCI compatibility tests

### Testing Commands Used
```bash
# List the specific commands you used to test this change
uv run pytest src/ -v
uv run pytest tests/ -v
uv run ruff check .
uv run mypy src tests
```

### Test Results
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Code coverage maintained/improved
- [ ] No linting errors
- [ ] Type checking passes

## Code Quality Checklist

### Component Architecture
- [ ] Changes follow the interface/implementation separation principle
- [ ] Dependency injection pattern maintained where applicable
- [ ] Protocol contracts not broken
- [ ] Components remain "forkliftable" (self-contained)

### Code Standards  
- [ ] Code follows project style guidelines (ruff formatting)
- [ ] All functions and classes have docstrings
- [ ] Type hints are present and accurate
- [ ] No unused imports or variables
- [ ] Error handling is appropriate

### Documentation
- [ ] README.md files updated if component APIs changed
- [ ] Code comments added for complex logic
- [ ] Component interaction documentation updated if needed

## CircleCI Status

- [ ] CircleCI build passes
- [ ] All quality gates met (linting, type checking, testing)
- [ ] Code coverage threshold maintained

**CircleCI Build Link:** [Paste link to successful CircleCI build]

**Coverage Report Link:** [Paste link to coverage report artifact]

## Authentication Testing

### Credentials Used (if applicable)
- [ ] Tested with local credential files (`credentials.json`, `token.json`)
- [ ] Tested with environment variables (CI/CD mode)
- [ ] Interactive authentication flow tested
- [ ] Non-interactive authentication flow tested

### Authentication Scenarios
- [ ] First-time OAuth2 setup works
- [ ] Token refresh works correctly
- [ ] Graceful handling of missing/invalid credentials
- [ ] CI/CD environment compatibility verified

## Breaking Changes

If this is a breaking change, describe:

1. **What breaks:** 
2. **Migration path:** 
3. **Backward compatibility:** 

## Additional Context

### Performance Impact
- [ ] No performance regression
- [ ] Performance improvement (describe)
- [ ] Performance impact acceptable (explain)

### Dependencies
- [ ] No new dependencies added
- [ ] New dependencies justified and documented
- [ ] Dependencies are pinned to specific versions

### Security Considerations
- [ ] No sensitive data exposed
- [ ] Authentication flows secure
- [ ] API credentials properly handled

## Screenshots (if applicable)

Add screenshots for UI changes or visual documentation updates.

## Reviewer Guidelines

### Focus Areas
Please pay special attention to:
- [ ] Component boundaries and interface contracts
- [ ] Authentication and credential handling
- [ ] Test coverage and quality
- [ ] Documentation accuracy

### Testing Instructions
1. Check out this branch
2. Run `uv sync` to install dependencies
3. Run the testing commands listed above
4. Verify the changes work as described

## Definition of Done

- [ ] Code follows project standards and passes all quality checks
- [ ] Tests are comprehensive and pass
- [ ] Documentation is updated and accurate
- [ ] CircleCI build is successful
- [ ] Changes are backward compatible OR migration path is documented
- [ ] Security implications have been considered
- [ ] Performance impact is acceptable
- [ ] Component architecture principles are maintained

---

**Additional Notes:**
Add any additional context, concerns, or questions for reviewers.
