# PurposePath Platform Monorepo

Multi-Language Microservices Architecture

## 🚨 Repository Structure Notice

This repository contains the **unified PurposePath platform** that combines both .NET and Python services into a single monorepo for better coordination and development workflow.

## 🏗️ Architecture Overview

PurposePath is a comprehensive business coaching and traction management platform built with a microservices architecture:

```
PurposePath Platform (Monorepo)
├── pp_api/         (.NET 8 - Account Service)
├── pp_ai/          (Python - AI Coaching & Traction Services) 
├── account/        (Streamlined .NET Account Deployment)
├── deployment/     (Legacy Deployment Templates)
└── docs/          (Shared Documentation)
```

## 🚀 Services

### Account Service (.NET 8 Lambda)

- **Location**: `pp_api/`
- **Responsibility**: Authentication, user management, billing, onboarding
- **Technology**: .NET 8, Clean Architecture, DynamoDB
- **Endpoints**: `/account/api/v1/*`

### AI Coaching Service (Python Lambda)

- **Location**: `pp_ai/`
- **Responsibility**: AI-powered business insights and coaching
- **Technology**: Python 3.11, FastAPI, AWS Lambda
- **Endpoints**: `/coaching/api/v1/*`

## 🛠️ Development Setup

### Prerequisites

- .NET 8 SDK
- Python 3.11+
- AWS CLI configured
- Git with submodule support

### Clone & Setup

```bash
# Clone the main repository
git clone https://github.com/mottych/PurposePath_Api.git
cd PurposePath_Api

# Setup .NET API
cd pp_api
dotnet restore
dotnet build

# Setup Python AI services
cd ../pp_ai
pip install -r requirements.txt
```

## 🏛️ Architecture Principles

### Clean Architecture Maintained

- **Domain-Driven Design**: Business logic in domain layer
- **Dependency Inversion**: Infrastructure depends on domain abstractions
- **Separation of Concerns**: Clear boundaries between layers and services

### Shared Infrastructure Pattern

- **Domain Models**: Single source of truth for business entities
- **Repository Layer**: Consistent data access across services
- **Common Utilities**: Shared middleware, configurations, and extensions

## 🚀 Deployment

PurposePath uses a **shared infrastructure pattern** that eliminates deployment complexity and enables seamless runtime switching.

### New Deployment Architecture

```
deployment/
├── shared-infrastructure/     # One-time AWS infrastructure
│   ├── template.yaml         # VPC, DynamoDB, Redis, Custom Domain
│   └── deploy-*.ps1          # Deployment scripts
└── account-service/          # Service-specific templates
    ├── template-dotnet.yaml  # .NET Lambda only
    ├── template-python.yaml  # Python Lambda only
    └── deploy-account.ps1    # Service deployment
```

### Quick Deployment

```powershell
# Deploy .NET Account Service (uses existing shared infrastructure)
.\deploy-account.ps1 -Stage dev
```

**Benefits:**
- ✅ **Uses existing infrastructure** - DynamoDB tables, JWT secrets, custom domain
- ✅ **Streamlined deployment** - single script, minimal template
- ✅ **Custom domain active** - `api.dev.purposepath.app` with service routing
- ✅ **Multi-service architecture** - .NET Account + Python Coaching/Traction

📖 **See [`deployment/README.md`](deployment/README.md) for complete deployment guide**

## 📊 Key Features Delivered

### ✅ Comprehensive UserPreferences System

- Strongly-typed preference management across all services
- Theme, language, timezone, and notification preferences
- Immutable value objects with comprehensive validation

### ✅ Zero Code Smells

- Eliminated all `object?` and `Dictionary<string, object?>` usage
- Strongly-typed filtering and query parameters
- Type-safe contracts throughout the application

### ✅ Multi-Lambda Architecture

- Independent service deployments
- Shared infrastructure and domain models
- Scalable microservices with clear boundaries

## 🔄 Git Workflow

### Unified Monorepo

```bash
# .NET API updates
git add pp_api/
git commit -m "feat: enhance account service"
git push origin platform-monorepo

# Python AI service updates  
git add pp_ai/
git commit -m "feat: improve coaching algorithms"
git push origin platform-monorepo

# Deployment updates
git add deployment/
git commit -m "infra: update shared infrastructure"
git push origin platform-monorepo
```

## 📋 Current Status

- ✅ Account Service: .NET 8 Lambda deployed to `api.dev.purposepath.app/account/`
- ✅ AI Coaching Service: Python Lambda deployed to `api.dev.purposepath.app/coaching/`
- ✅ Traction Service: Python Lambda deployed to `api.dev.purposepath.app/traction/`
- ✅ Infrastructure: Shared DynamoDB tables, JWT secrets, custom domain
- ✅ Deployment: Streamlined single-script deployment
- ✅ Documentation: Updated with current architecture

## 🏆 Development Standards

- **Clean Architecture**: Domain-driven design principles
- **Type Safety**: Comprehensive strongly-typed models
- **Test Coverage**: Unit and integration tests
- **Code Quality**: Zero warnings with `--warnaserror`
- **Documentation**: Technical and architectural documentation

---

**Last Updated**: September 29, 2025  
**Version**: 2.1 (Shared Infrastructure Architecture)  
**Team**: PurposePath Development Team
