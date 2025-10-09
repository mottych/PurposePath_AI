#!/bin/bash
# PurposePath Platform Setup Script
# This script sets up the complete monorepo for development

echo "🚀 Setting up PurposePath Platform Monorepo..."
echo "================================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Git
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check .NET
if ! command -v dotnet &> /dev/null; then
    echo "❌ .NET SDK is not installed. Please install .NET 8 SDK first."
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

echo "✅ All prerequisites are installed"

# Clone repository if not already cloned
if [ ! -d ".git" ]; then
    echo "📁 Cloning PurposePath repository..."
    git clone https://github.com/mottych/PurposePath_Api.git .
    
    echo "🔄 Switching to platform-monorepo branch..."
    git checkout platform-monorepo
else
    echo "📁 Repository already exists, updating..."
    git fetch origin
    git checkout platform-monorepo
    git pull origin platform-monorepo
fi

# Initialize submodules
echo "🔧 Initializing git submodules..."
git submodule init
git submodule update

# Setup .NET API
echo "🏗️ Setting up .NET API services..."
cd pp_api
dotnet restore
dotnet build --configuration Release --warnaserror
echo "✅ .NET API services built successfully"

# Run .NET tests
echo "🧪 Running .NET tests..."
dotnet test --no-build --configuration Release
if [ $? -eq 0 ]; then
    echo "✅ All .NET tests passed"
else
    echo "❌ Some .NET tests failed"
    exit 1
fi

# Setup Python AI services
echo "🐍 Setting up Python AI services..."
cd ../pp_ai_submodule

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Python AI services setup completed"

# Return to root
cd ..

echo ""
echo "🎉 PurposePath Platform Setup Complete!"
echo "========================================"
echo ""
echo "📂 Repository Structure:"
echo "  ├── pp_api/           (.NET 8 Account Services)"
echo "  ├── pp_ai_submodule/  (Python AI Services)"
echo "  └── docs/            (Platform Documentation)"
echo ""
echo "🚀 Next Steps:"
echo "  1. Review docs/MIGRATION_STATUS.md for platform overview"
echo "  2. Check docs/GIT_WORKFLOW.md for development workflow"
echo "  3. Start developing with the unified platform!"
echo ""
echo "💡 Development Commands:"
echo "  .NET API: cd pp_api && dotnet run"
echo "  Python AI: cd pp_ai_submodule && python main.py"
echo ""