# Development Guide

## Setting up development environment

### Backend

The backend is a Django REST API built with Python. To set up the backend development environment:

#### Prerequisites

1. **Python 3.9+** - The project uses Python 3.9 or higher
2. **PostgreSQL** - Required for the database backend
   ```bash
   brew install postgresql
   ```

#### Virtual Environment Setup

1. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r service/requirements.txt
   ```

#### IDE Configuration

To enable proper IntelliSense, jump-to-definition, and other IDE features in Cursor (or VS Code):

1. **Configure Python interpreter:**
   - Press `Cmd+Shift+P` and type "Python: Select Interpreter"
   - Select the interpreter at `./.venv/bin/python`

2. **Project configuration files:**
   - `.vscode/settings.json` - Configures the Python interpreter and analysis settings
   - `pyrightconfig.json` - Provides type checking and IntelliSense configuration
