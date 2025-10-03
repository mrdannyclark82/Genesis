#!/usr/bin/env python
"""Test script to demonstrate LLM integration with nvidia/nemotron-nano-9b-v2:free."""

import asyncio
import os
from core.agent import GenesisAgent
from core.config import Config
from llm.client import LLMClient

async def test_llm_direct():
    """Test LLM client directly."""
    print("=" * 60)
    print("Testing LLM Client Direct Communication")
    print("=" * 60)
    
    config = Config()
    
    # Check if API key is set
    if not config.openrouter_api_key:
        print("\n⚠️  OpenRouter API key not set!")
        print("To enable LLM features:")
        print("1. Get a free API key from https://openrouter.ai/")
        print("2. Add it to .env as: OPENROUTER_API_KEY=your_key_here")
        print("3. The model nvidia/nemotron-nano-9b-v2:free is free to use!")
        print("\nSkipping LLM test (will use fallback responses)\n")
        return False
    
    llm = LLMClient(config)
    
    async with llm:
        # Test simple question
        print(f"\n🤖 Using model: {llm.model}")
        print("\n📝 Question: What is Python used for?")
        
        response = await llm.answer_question("What is Python used for? Give a brief answer.")
        
        if response:
            print(f"\n💬 Response:\n{response}")
            return True
        else:
            print("\n❌ Failed to get response from LLM")
            return False

async def test_agent_with_llm():
    """Test agent with LLM integration."""
    print("\n" + "=" * 60)
    print("Testing Genesis Agent with LLM Integration")
    print("=" * 60)
    
    config = Config()
    agent = GenesisAgent(config)
    
    # Test natural language processing
    test_queries = [
        "What can you do?",
        "Explain what async functions are in Python",
        "How can I improve my code quality?"
    ]
    
    for query in test_queries:
        print(f"\n📝 User: {query}")
        response = await agent.process_natural_language(query)
        print(f"🤖 Genesis: {response[:200]}..." if len(response) > 200 else f"🤖 Genesis: {response}")

async def main():
    """Run all tests."""
    print("\n🚀 Genesis AI Agent - LLM Integration Test")
    print(f"Model: nvidia/nemotron-nano-9b-v2:free (via OpenRouter)\n")
    
    # Test direct LLM client
    llm_works = await test_llm_direct()
    
    # Test agent integration
    await test_agent_with_llm()
    
    print("\n" + "=" * 60)
    if llm_works:
        print("✅ All tests completed successfully!")
    else:
        print("⚠️  Tests completed with fallback responses")
        print("   Set OPENROUTER_API_KEY to enable full LLM features")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
