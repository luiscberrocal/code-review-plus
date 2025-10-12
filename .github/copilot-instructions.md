# code-review-plus Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-12

## Constitution Compliance

All development must adhere to the project constitution principles:
- **Pluggable Architecture**: Standardized plugin interfaces with version compatibility
- **CLI-First Design**: Unix philosophy with comprehensive CLI support  
- **Rule-Based Analysis**: Configurable rules with hierarchical precedence
- **Comprehensive Reporting**: Pluggable format providers (markdown, HTML, JSON, XML, text) with templating
- **Code Quality Standards**: Python-specific tools with 85% test coverage + stochastic testing requirements
- **Pluggable Notification Architecture**: Configurable delivery via email, Slack, Teams, webhooks with templating
- **Python-Specific Requirements**: Python 3.10+, pytest, mypy, hypothesis integration

## Active Technologies
- Python 3.10+ (from constitution requirements) + pydantic (for existing schemas), coverage.py (for coverage analysis) (003-rule-validation-reporting)

## Project Structure
```
src/
tests/
```

## Plugin Development Guidelines

When developing plugins:
- Implement standardized interfaces with clear contracts
- Include metadata with supported file types and dependencies
- Follow security constraints and resource limits
- Provide comprehensive documentation and examples

## Python Development Standards

All Python code must follow constitution requirements:
- Use Python 3.10+ with full type hints and mypy validation
- Achieve minimum 85% test coverage using pytest and coverage.py
- Include stochastic tests using hypothesis for non-deterministic components
- Follow ruff linting and formatting standards
- Support pyproject.toml configuration format
- Include proper error handling and input validation

## Report Format Plugin Guidelines

When developing report format plugins:
- Support templating with customizable organizational branding
- Implement standard metadata schema for report content
- Follow accessibility guidelines for HTML/markdown outputs
- Provide validation for template syntax and content structure

## Notification Plugin Guidelines

When developing notification plugins:
- Implement rate limiting and retry mechanisms
- Support templatable content with channel-specific formatting
- Filter sensitive information per configurable policies
- Provide clear error handling and delivery status reporting

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Python 3.10+ (from constitution requirements): Follow standard conventions

## Recent Changes
- 003-rule-validation-reporting: Added Python 3.10+ (from constitution requirements) + pydantic (for existing schemas), coverage.py (for coverage analysis)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->