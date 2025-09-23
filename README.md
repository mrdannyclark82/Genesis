# Genesis AI Coding Agent

A fully functional self-improving AI virtual assistant coding agent that can interact with GitHub repositories, create code, suggest improvements, and implement changes.

## Features

- **GitHub Integration**: Full interaction with GitHub repositories, issues, pull requests, and workflows
- **Code Analysis**: Analyze existing code and suggest improvements
- **Code Generation**: Create new code based on requirements and patterns
- **Self-Improvement**: Learn from interactions and improve suggestions over time
- **Interactive Interface**: Command-line interface with text input and feedback loops

## Installation

```bash
# Clone the repository
git clone https://github.com/mrdannyclark82/Genesis.git
cd Genesis

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your GitHub token and other configurations
```

## Usage

```bash
# Start the interactive AI assistant
python genesis.py

# Run specific commands
python genesis.py --analyze /path/to/code
python genesis.py --suggest-improvements
python genesis.py --implement-changes
```

## Configuration

Copy `.env.example` to `.env` and configure:

- `GITHUB_TOKEN`: Your GitHub personal access token
- `OPENAI_API_KEY`: OpenAI API key for AI capabilities (optional)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Architecture

- `genesis.py`: Main entry point and CLI interface
- `core/`: Core AI agent functionality
- `github_api/`: GitHub API integration
- `code_analyzer/`: Code analysis and suggestion engine
- `self_improvement/`: Learning and improvement mechanisms
- `utils/`: Utility functions and helpers

## License

MIT License
