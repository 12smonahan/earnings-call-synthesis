# earnings-call-synthesis
Uses Seeking Alpha API to synthesize earnings call transcripts and send email triggers to users

## Setup

This project uses Python 3.12 and Poetry for dependency management.

### Prerequisites

1. **Install Python 3.12**
   - On macOS: `brew install python@3.12` (requires Homebrew)
   - Or download from [python.org](https://www.python.org/downloads/)
   - Or use pyenv: `pyenv install 3.12`

2. **Install Poetry** (if not already installed)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
   Add Poetry to your PATH:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

### Creating the Virtual Environment

Once Python 3.12 is installed, create the virtual environment:

```bash
# Make sure Poetry is in your PATH
export PATH="$HOME/.local/bin:$PATH"

# Create virtual environment with Python 3.12
poetry env use python3.12

# Install dependencies (when you add them)
poetry install
```

The virtual environment will be created in `.venv/` directory within the project (configured via Poetry settings).

### Using the Virtual Environment

```bash
# Activate the environment
poetry shell

# Or run commands within the environment
poetry run python <script>
```
