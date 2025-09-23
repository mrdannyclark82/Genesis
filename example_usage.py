#!/usr/bin/env python3
"""
Example usage of Genesis AI Coding Agent.
This demonstrates the basic functionality without requiring actual API keys.
"""

import asyncio
import tempfile
from pathlib import Path

from core.config import Config
from core.agent import GenesisAgent


async def demo_code_analysis():
    """Demonstrate code analysis capabilities."""
    print("🔍 Code Analysis Demo")
    print("=" * 50)
    
    # Create a temporary Python file with some issues
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
# Example Python file with some issues

def function_without_docstring(x, y):
    # TODO: Add proper error handling
    result = x + y
    console.log("This is wrong - not JavaScript!")  # Wrong language
    return result

class MyClass:
    def __init__(self, value):
        self.value = value
        
    def very_long_method_name_that_exceeds_recommended_length_and_should_be_flagged(self):
        return "This line is also very long and exceeds the recommended character limit for readability"

# Unused variable
unused_var = "This variable is never used"

# Missing docstring for class
class AnotherClass:
    pass
""")
        temp_file = f.name
    
    try:
        # Create config without requiring actual tokens for demo
        config = Config(
            github_token='demo_token',  # Fake token for demo
            learning_enabled=True
        )
        
        # Initialize agent components individually to avoid GitHub API calls
        from code_analyzer.analyzer import CodeAnalyzer
        from self_improvement.learner import SelfLearner
        
        analyzer = CodeAnalyzer(config)
        learner = SelfLearner(config)
        
        # Analyze the code
        print(f"Analyzing file: {temp_file}")
        results = await analyzer.analyze_path(temp_file)
        
        print("\n📋 Analysis Results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result}")
        
        # Generate suggestions
        print(f"\n💡 Improvement Suggestions:")
        suggestions = await analyzer.suggest_improvements(str(Path(temp_file).parent))
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        # Show learning system info
        print(f"\n📊 Learning System:")
        insights = await learner.get_learning_insights()
        print(f"  Learning enabled: {config.learning_enabled}")
        print(f"  Storage path: {config.feedback_storage_path}")
    
    finally:
        # Clean up
        Path(temp_file).unlink(missing_ok=True)


async def demo_natural_language_processing():
    """Demonstrate natural language processing."""
    print("\n🗣️  Natural Language Processing Demo")
    print("=" * 50)
    
    # Show what the NLP system would do (without actually running it)
    test_inputs = [
        "Can you analyze this code for me?",
        "What improvements do you suggest?", 
        "Explain what this function does",
        "How can I make my code better?",
        "What are some best practices for Python?",
    ]
    
    for user_input in test_inputs:
        print(f"\n👤 User: {user_input}")
        
        # Simulate intent parsing
        if 'analyze' in user_input.lower():
            print(f"🤖 Genesis: I'll analyze your code and identify potential issues.")
        elif 'suggest' in user_input.lower() or 'improve' in user_input.lower():
            print(f"🤖 Genesis: I can suggest improvements based on code analysis.")
        elif 'explain' in user_input.lower():
            print(f"🤖 Genesis: I can explain code functionality and structure.")
        else:
            print(f"🤖 Genesis: I'm here to help with code analysis and improvements.")


async def demo_learning_system():
    """Demonstrate the self-learning system."""
    print("\n🧠 Self-Learning System Demo")
    print("=" * 50)
    
    config = Config(
        github_token='demo_token',
        learning_enabled=True
    )
    
    from self_improvement.learner import SelfLearner
    learner = SelfLearner(config)
    
    # Simulate some learning interactions
    print("Simulating learning from feedback...")
    
    feedback_examples = [
        "Your suggestions for adding docstrings were very helpful!",
        "The code analysis found real issues in my project",
        "I'd like to see more performance optimization suggestions",
        "The style recommendations helped improve code readability",
    ]
    
    for feedback in feedback_examples:
        await learner.learn_from_feedback(feedback)
        print(f"  ✅ Learned from: {feedback[:50]}...")
    
    # Get learning insights
    insights = await learner.get_learning_insights()
    
    print(f"\n📈 Learning Insights:")
    for key, value in insights.items():
        if key != 'patterns':  # Skip detailed patterns for demo
            print(f"  {key}: {value}")


async def main():
    """Run all demos."""
    print("🚀 Genesis AI Coding Agent - Demo")
    print("=" * 60)
    print("This demo shows the capabilities without requiring API keys.")
    print("For full functionality, configure your .env file with actual tokens.\n")
    
    try:
        await demo_code_analysis()
        await demo_natural_language_processing()
        await demo_learning_system()
        
        print("\n✨ Demo completed successfully!")
        print("\nTo use Genesis with real GitHub repositories:")
        print("1. Copy .env.example to .env")
        print("2. Add your GitHub token and other API keys")
        print("3. Run: python genesis.py")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("This is expected without proper API configuration.")


if __name__ == "__main__":
    asyncio.run(main())