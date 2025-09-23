# Genesis AI Coding Agent - Quick Start Guide

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your GitHub token and other API keys
```

### 3. Run the Demo (No API Keys Required)
```bash
python example_usage.py
```

### 4. Start Interactive Mode
```bash
python genesis.py
# or
python genesis.py interactive
```

## 🎯 Available Commands

### CLI Commands
- `python genesis.py analyze /path/to/code` - Analyze code files
- `python genesis.py suggest-improvements` - Get improvement suggestions
- `python genesis.py implement-changes` - Apply suggested changes
- `python genesis.py interactive` - Start interactive mode

### Interactive Mode Commands
- `help` - Show available commands
- `analyze` - Analyze current directory
- `suggest` - Get improvement suggestions
- `implement` - Implement suggested changes
- `status` - Show agent status
- `learn` - Enter learning mode
- `quit` - Exit the assistant

## 💡 Key Features Demonstrated

### Code Analysis
The agent can analyze multiple programming languages and identify:
- Missing docstrings
- Style violations
- Long functions/lines
- TODO/FIXME comments
- Security issues
- Performance problems

### GitHub Integration
Full interaction with GitHub repositories:
- Repository structure analysis
- Issue and PR management
- Workflow monitoring
- File updates and commits

### Self-Learning
The agent learns from:
- User feedback
- Implementation success rates
- Code analysis patterns
- Interaction history

### Natural Language Processing
Understands commands like:
- "Can you analyze this code for me?"
- "What improvements do you suggest?"
- "Explain what this function does"

## 🔧 Configuration Options

Edit `.env` to configure:
- `GITHUB_TOKEN` - GitHub personal access token
- `OPENAI_API_KEY` - For enhanced AI capabilities
- `LOG_LEVEL` - Logging verbosity
- `LEARNING_ENABLED` - Enable/disable self-improvement

## 📊 Example Output

```
🔍 Code Analysis Demo
==================================================
Analyzing file: /tmp/example.py

📋 Analysis Results:
  1. Missing docstring in function_without_docstring at line 4
  2. TODO/FIXME comment found at line 5
  3. Long line at 15 (150 characters)

💡 Improvement Suggestions:
  1. Add docstring to explain what function_without_docstring does
  2. Address TODO item or convert to proper issue tracking
  3. Break long line into multiple lines for readability
```

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/
```

## 🤝 Contributing

The Genesis AI Agent is designed to be self-improving. It learns from:
- Your usage patterns
- Feedback you provide
- Success/failure of implementations
- Code analysis results

The more you use it, the better it becomes at helping you!