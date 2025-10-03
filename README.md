# Genesis AI Coding Agent

A fully functional self-improving AI virtual assistant coding agent that can interact with GitHub repositories, create code, suggest improvements, and implement changes.

## Features

- **GitHub Integration**: Full interaction with GitHub repositories, issues, pull requests, and workflows
- **Code Analysis**: Analyze existing code and suggest improvements
- **Code Generation**: Create new code based on requirements and patterns
- **AI-Powered Responses**: Uses nvidia/nemotron-nano-9b-v2:free LLM for intelligent, context-aware assistance
- **Self-Improvement**: Learn from interactions and improve suggestions over time
- **Interactive Interface**: Command-line interface with text input and feedback loops
- **Persona System**: Switch between different AI personas for varied interaction styles
- **External Search**: Search GitHub, Stack Overflow, and other sources for code examples

## Quick Start

See [QUICKSTART_LLM.md](QUICKSTART_LLM.md) for a 3-step guide to enable AI-powered features with nvidia/nemotron-nano-9b-v2:free.

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
- `OPENROUTER_API_KEY`: OpenRouter API key for AI capabilities (required for LLM features)
- `LLM_MODEL`: AI model to use (default: nvidia/nemotron-nano-9b-v2:free)
- `OPENAI_API_KEY`: OpenAI API key (optional, legacy support)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Getting an OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add it to your `.env` file as `OPENROUTER_API_KEY`

The default model `nvidia/nemotron-nano-9b-v2:free` is free to use through OpenRouter.

## Architecture

- `genesis.py`: Main entry point and CLI interface
- `core/`: Core AI agent functionality
- `llm/`: LLM client for AI model integration
- `github_api/`: GitHub API integration
- `code_analyzer/`: Code analysis and suggestion engine
- `self_improvement/`: Learning and improvement mechanisms
- `utils/`: Utility functions and helpers

## Documentation

- [Quick Start Guide](QUICKSTART_LLM.md) - 3-step setup for LLM features
- [LLM Integration Guide](LLM_INTEGRATION.md) - Comprehensive LLM documentation
- [Feature Installation Guide](FEATURE_INSTALLATION_GUIDE.md) - Installing additional features
- [Enhanced Features](ENHANCED_FEATURES.md) - Advanced capabilities

## License

MIT License
