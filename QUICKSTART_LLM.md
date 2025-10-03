# Quick Start: nvidia/nemotron-nano-9b-v2:free Setup

This guide will help you quickly set up Genesis to use the nvidia/nemotron-nano-9b-v2:free AI model.

## ⚡ Quick Setup (3 steps)

### Step 1: Get Your Free API Key

Visit https://openrouter.ai/ and:
1. Sign up for a free account
2. Go to "API Keys" section
3. Create a new API key
4. Copy the key (starts with `sk-or-v1-...`)

### Step 2: Configure Genesis

```bash
# In your Genesis directory
cp .env.example .env

# Edit .env and add your API key
echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" >> .env
```

### Step 3: Test It!

```bash
python test_llm_integration.py
```

You should see:
```
✅ All tests completed successfully!
```

## 🎯 What You Get

With nvidia/nemotron-nano-9b-v2:free, you get:

- ✅ **Free to use** - No credit card required
- ✅ **Fast responses** - Optimized for coding tasks  
- ✅ **Intelligent code analysis** - AI-powered code reviews
- ✅ **Natural language queries** - Ask coding questions naturally
- ✅ **Feature suggestions** - AI-generated improvement ideas
- ✅ **Context-aware assistance** - Understands your project

## 💬 Example Usage

### Interactive Mode

```bash
python genesis.py
```

Then try these commands:
```
> What are Python decorators and when should I use them?
> How can I improve error handling in my code?
> Suggest some features for a web application
> Explain async/await to me
```

### Programmatic Usage

```python
import asyncio
from core.agent import GenesisAgent

async def demo():
    agent = GenesisAgent()
    
    response = await agent.process_natural_language(
        "What are best practices for REST API design?"
    )
    print(response)

asyncio.run(demo())
```

## 🔧 Verify Your Setup

Run these commands to check everything:

```bash
# Check configuration is loaded
python -c "from core.config import Config; c=Config.from_env(); print(f'Model: {c.llm_model}')"

# Should print: Model: nvidia/nemotron-nano-9b-v2:free

# Check LLM client works
python -c "
from llm.client import LLMClient
from core.config import Config
c = Config.from_env()
llm = LLMClient(c)
print(f'✓ LLM ready with model: {llm.model}')
"
```

## 🎓 Learn More

- Full documentation: See `LLM_INTEGRATION.md`
- Available features: See `README.md`
- API reference: See `llm/client.py`

## ❓ Troubleshooting

**Problem**: "OpenRouter API key not set" warning

**Solution**: Make sure you added the key to `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

**Problem**: "Error making LLM request"

**Solutions**:
1. Check your internet connection
2. Verify your API key is valid at https://openrouter.ai/
3. Make sure you're using the correct model name: `nvidia/nemotron-nano-9b-v2:free`

## 💡 Tips

1. **Start Free**: The nvidia/nemotron model is completely free
2. **Experiment**: Try different questions to see what it can do
3. **Combine Features**: Use LLM with code analysis for best results
4. **Check Logs**: Run with `LOG_LEVEL=DEBUG` to see what's happening

## 🚀 Next Steps

Once you have it working:

1. Try the interactive mode: `python genesis.py`
2. Ask questions about your code
3. Get AI-powered feature suggestions
4. Explore other OpenRouter models (if needed)

For more advanced usage and configuration options, see `LLM_INTEGRATION.md`.

---

**Need Help?** 
- Check the logs for error messages
- Review the full documentation in `LLM_INTEGRATION.md`
- Open an issue on GitHub with your question
