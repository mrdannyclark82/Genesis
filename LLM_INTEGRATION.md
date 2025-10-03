# LLM Integration Guide

## Overview

Genesis AI Agent now supports integration with AI language models via OpenRouter. By default, it uses the **nvidia/nemotron-nano-9b-v2:free** model, which is completely free to use through OpenRouter.

## Features

The LLM integration enhances Genesis with:

- **Intelligent Natural Language Responses**: Get context-aware answers to your coding questions
- **Code Analysis**: AI-powered code review and suggestions
- **Improvement Suggestions**: Intelligent recommendations for project enhancements
- **Feature Suggestions**: AI-generated ideas for new features
- **Conversational Interface**: Natural dialogue with the AI assistant

## Setup

### 1. Get an OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for a free account
3. Navigate to your API Keys section
4. Create a new API key

### 2. Configure Genesis

Add your OpenRouter API key to the `.env` file:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here

# Optional: Change the model (default is nvidia/nemotron-nano-9b-v2:free)
LLM_MODEL=nvidia/nemotron-nano-9b-v2:free
```

### 3. Test the Integration

Run the test script to verify everything is working:

```bash
python test_llm_integration.py
```

## Available Models

The system is configured to use OpenRouter, which supports many models. The default free model is:

- **nvidia/nemotron-nano-9b-v2:free** (Recommended - Free)
  - Fast and efficient
  - No cost
  - Good for general coding tasks

You can also use other models by setting the `LLM_MODEL` environment variable:

```bash
# Other free models available on OpenRouter
LLM_MODEL=google/gemini-flash-1.5-8b:free
LLM_MODEL=meta-llama/llama-3.2-3b-instruct:free

# Premium models (require credits)
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_MODEL=openai/gpt-4-turbo
```

## Usage Examples

### Interactive Mode

Start Genesis in interactive mode and ask questions:

```bash
python genesis.py
```

Then type queries like:
- "What is the best way to handle errors in Python?"
- "Explain async functions to me"
- "How can I improve my code quality?"
- "Suggest some features for my project"

### Programmatic Usage

Use the LLM client directly in your Python code:

```python
import asyncio
from core.config import Config
from llm.client import LLMClient

async def main():
    config = Config.from_env()
    llm = LLMClient(config)
    
    async with llm:
        # Ask a question
        response = await llm.answer_question(
            "What are Python decorators?"
        )
        print(response)
        
        # Analyze code
        code = """
def calculate(x, y):
    return x + y
        """
        analysis = await llm.generate_code_analysis(code, language="python")
        print(analysis)

asyncio.run(main())
```

### Use with GenesisAgent

```python
import asyncio
from core.agent import GenesisAgent

async def main():
    agent = GenesisAgent()
    
    # Natural language processing with LLM
    response = await agent.process_natural_language(
        "What are the best practices for API design?"
    )
    print(response)

asyncio.run(main())
```

## Fallback Behavior

If the OpenRouter API key is not configured, Genesis will:

1. Log a warning message
2. Use predefined response templates for common queries
3. Continue to work with rule-based analysis and suggestions

This ensures the system remains functional even without LLM access.

## Cost Considerations

- **nvidia/nemotron-nano-9b-v2:free**: Completely free, no credit card required
- **Other free models**: Available on OpenRouter with the `:free` suffix
- **Premium models**: Require OpenRouter credits (pay-as-you-go)

Check [OpenRouter Pricing](https://openrouter.ai/pricing) for current rates.

## Troubleshooting

### "OpenRouter API key not set" Warning

**Solution**: Add your API key to the `.env` file:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### "Error making LLM request" Error

**Possible causes**:
1. Invalid API key - Check your OpenRouter dashboard
2. Network connectivity issues - Verify internet connection
3. Model not available - Try the default model: `nvidia/nemotron-nano-9b-v2:free`

**Solution**: Check the logs for specific error messages and verify your configuration.

### Rate Limiting

OpenRouter implements rate limits. If you exceed them:
1. Wait a few moments and retry
2. Consider using a different model
3. Check your OpenRouter dashboard for usage limits

## Advanced Configuration

### Custom System Prompts

You can customize the system prompts by modifying the LLM client methods:

```python
# In llm/client.py
system_prompt = """You are an expert Python developer.
Focus on writing clean, efficient, and well-documented code.
Always explain your reasoning."""
```

### Adjusting Parameters

Modify temperature and max_tokens for different response styles:

```python
response = await llm.chat_completion(
    messages=[{"role": "user", "content": "Your question"}],
    temperature=0.3,  # Lower = more focused, Higher = more creative
    max_tokens=2000   # Maximum response length
)
```

### Using Multiple Models

You can instantiate multiple LLM clients with different models:

```python
config = Config.from_env()

# Fast model for quick responses
config.llm_model = "nvidia/nemotron-nano-9b-v2:free"
fast_llm = LLMClient(config)

# More capable model for complex tasks
config.llm_model = "anthropic/claude-3.5-sonnet"
advanced_llm = LLMClient(config)
```

## API Reference

### LLMClient Methods

#### `chat_completion(messages, temperature=0.7, max_tokens=1000, system_prompt=None)`
Send a chat completion request.

#### `generate_code_analysis(code, language="python")`
Analyze code and provide feedback.

#### `generate_improvement_suggestions(project_description)`
Generate improvement suggestions for a project.

#### `answer_question(question, context=None)`
Answer a coding question with optional context.

#### `generate_feature_suggestions(project_info)`
Suggest new features based on project information.

## Security Notes

1. **Never commit your API key** to version control
2. Use the `.env` file (which is in `.gitignore`)
3. Rotate your API keys periodically
4. Monitor your OpenRouter usage dashboard

## Support

For issues or questions:
1. Check the logs: Look for warnings and errors
2. Review [OpenRouter Documentation](https://openrouter.ai/docs)
3. Open an issue on the Genesis GitHub repository
