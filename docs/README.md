# PurposePath AI Documentation

## 🎯 Project Overview

PurposePath AI is a Python-based AI coaching microservices platform that provides intelligent coaching conversations, business insights, and strategic guidance through advanced LLM integration.

## 📚 Documentation Structure

This documentation is organized into four main categories:

### 📖 Guides (`/docs/Guides/`)
General directions and instructions that are always applicable across the project:

- **[Branching Strategy](./Guides/BRANCHING_STRATEGY.md)** - Three-tier branching workflow (master/staging/dev)
- **[Development Guide](./Guides/DEVELOPMENT_GUIDE.md)** - Development workflow and best practices
- **[Development Standards](./Guides/DEVELOPMENT_STANDARDS.md)** - Coding standards and conventions
- **[Engineering Guide](./Guides/ENGINEERING_GUIDE.md)** - Technical architecture and patterns
- **[Clean Architecture & DDD Guidelines](./Guides/clean-architecture-ddd-guidelines.md)** - Architecture principles
- **[Shared Types Guide](./Guides/shared-types-guide.md)** - Type system and shared type usage

### 📋 Plans (`/docs/Plans/`)
Active architecture and plans for development (move to Archive when completed):

- **[AI Coaching Architecture Design](./Plans/AI_COACHING_ARCHITECTURE_DESIGN.md)** - AI coaching system architecture
- **[AI Coaching Implementation Plan](./Plans/AI_COACHING_IMPLEMENTATION_PLAN.md)** - Implementation roadmap
- **[Coaching Service Requirements](./Plans/COACHING_SERVICE_REQUIREMENTS.md)** - Service specifications
- **[Future Architecture](./Plans/FUTURE_ARCHITECTURE.md)** - Long-term architectural vision
- **[Coaching Service Endpoints](./Plans/coaching-service-endpoints.md)** - API endpoint specifications
- **[Frontend Integration Guide](./Plans/frontend-integration-guide.md)** - Frontend integration patterns

### 📊 Status (`/docs/Status/`)
Summaries of actions performed and progress tracking:

- **[Implementation Summary](./Status/IMPLEMENTATION_SUMMARY.md)** - Current implementation status
- **[Branching Implementation](./Status/BRANCHING_IMPLEMENTATION.md)** - Git repository setup and branching strategy implementation

### 📦 Archive (`/docs/Archive/`)
Completed architecture and plans (moved from Plans when finished)

## 🚀 Quick Start

### 1. Repository Setup

```bash
# Clone the repository
git clone https://github.com/mottych/PurposePath_AI.git
cd PurposePath_AI

# Checkout development branch
git checkout dev
```

### 2. Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (coaching service example)
cd coaching
pip install -r requirements-dev.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 3. Running Services

```bash
# Run coaching service locally
cd coaching
python -m uvicorn src.api.main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Check code quality
mypy src/
black --check src/
```

### 4. Start Development

```bash
# Create feature branch from dev
git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name

# Make changes, test, commit
git add .
git commit -m "feat(scope): description"
git push -u origin feature/your-feature-name
```

## 📊 Repository Information

### Repository Structure

```
PurposePath_AI/
├── coaching/           # AI coaching service (Python/FastAPI)
├── shared/            # Shared types and utilities
├── docs/              # Documentation
│   ├── Guides/       # Development guides
│   ├── Plans/        # Feature specifications
│   ├── Status/       # Progress tracking
│   └── Archive/      # Historical documents
├── infra/            # Infrastructure as code
└── deployment/       # Deployment configurations
```

### Key Services

- **Coaching Service** - AI-powered coaching conversations and insights
- **Shared Infrastructure** - Common types, models, and utilities

## 🛠️ Development Tools

### Recommended VS Code Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylance",
    "ms-python.mypy-type-checker",
    "ms-python.black-formatter",
    "ms-python.isort",
    "GitHub.copilot"
  ]
}
```

### Code Quality Tools

```bash
# Type checking
mypy src/

# Code formatting
black src/
isort src/

# Linting
flake8 src/

# Testing with coverage
pytest --cov=src --cov-report=html
```

## 🌿 Branching Strategy

This repository follows a three-tier branching strategy:

- **`master`** - Production environment (stable releases)
- **`staging`** - Staging environment (pre-production validation)
- **`dev`** - Development environment (active development)

All feature development should branch from `dev`. See the [Branching Strategy Guide](./Guides/BRANCHING_STRATEGY.md) for complete workflow details.

### Quick Branch Commands

```bash
# Start new feature
git checkout dev && git pull origin dev
git checkout -b feature/your-feature-name

# Complete and merge feature
git checkout dev
git merge feature/your-feature-name --no-ff
git push origin dev
```

---

## 📞 Quick Commands Reference

```bash
# Development Workflow
git checkout dev                                    # Switch to dev branch
git pull origin dev                                 # Get latest changes
git checkout -b feature/name                        # Create feature branch
pytest tests/ -v                                    # Run tests
mypy src/                                          # Type check
git commit -m "feat(scope): description"           # Commit with convention

# Service Operations
cd coaching && uvicorn src.api.main:app --reload   # Run coaching service
pytest --cov=src --cov-report=html                 # Test with coverage
python -m src.api.main                             # Direct Python run

# Code Quality
black src/                                         # Format code
isort src/                                         # Sort imports
flake8 src/                                        # Lint code
mypy src/ --strict                                 # Strict type checking
```

---

## 📚 Additional Resources

- **Repository**: https://github.com/mottych/PurposePath_AI
- **Branching Guide**: [docs/Guides/BRANCHING_STRATEGY.md](./Guides/BRANCHING_STRATEGY.md)
- **Development Standards**: [docs/Guides/DEVELOPMENT_STANDARDS.md](./Guides/DEVELOPMENT_STANDARDS.md)
- **Engineering Guide**: [docs/Guides/ENGINEERING_GUIDE.md](./Guides/ENGINEERING_GUIDE.md)

---

**Repository Status:** ✅ Active Development  
**Documentation Version:** 2.0  
**Last Updated:** October 8, 2025
