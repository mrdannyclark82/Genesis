#!/usr/bin/env python3
"""
Genesis AI Coding Agent
A fully functional self-improving AI virtual assistant coding agent.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.prompt import Prompt
from dotenv import load_dotenv

from core.agent import GenesisAgent
from core.config import Config
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

console = Console()
logger = setup_logger(__name__)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config', type=click.Path(), help='Path to config file')
@click.pass_context
def cli(ctx, debug, config):
    """Genesis AI Coding Agent - Your intelligent coding assistant."""
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    ctx.obj['config_path'] = config


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive mode with the AI assistant."""
    console.print("[bold green]🚀 Genesis AI Coding Agent[/bold green]")
    console.print("Welcome! I'm your AI coding assistant. Type 'help' for commands or 'quit' to exit.\n")
    
    try:
        agent = GenesisAgent()
        asyncio.run(run_interactive_session(agent))
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye! 👋[/yellow]")
    except Exception as e:
        logger.error(f"Error in interactive mode: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.pass_context
def analyze(ctx, path):
    """Analyze code at the specified path."""
    console.print(f"[blue]Analyzing code at: {path}[/blue]")
    
    try:
        agent = GenesisAgent()
        results = asyncio.run(agent.analyze_code(path))
        
        console.print("\n[bold]Analysis Results:[/bold]")
        for result in results:
            console.print(f"• {result}")
            
    except Exception as e:
        logger.error(f"Error analyzing code: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('repo_url', required=False)
@click.pass_context
def suggest_improvements(ctx, repo_url):
    """Suggest improvements for the current repository or specified repo."""
    if repo_url:
        console.print(f"[blue]Analyzing repository: {repo_url}[/blue]")
    else:
        console.print("[blue]Analyzing current repository...[/blue]")
    
    try:
        agent = GenesisAgent()
        suggestions = asyncio.run(agent.suggest_improvements(repo_url))
        
        console.print("\n[bold]Improvement Suggestions:[/bold]")
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"{i}. {suggestion}")
            
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--auto-approve', is_flag=True, help='Auto-approve all changes')
@click.pass_context
def implement_changes(ctx, auto_approve):
    """Implement suggested improvements."""
    console.print("[blue]Implementing suggested changes...[/blue]")
    
    try:
        agent = GenesisAgent()
        results = asyncio.run(agent.implement_changes(auto_approve=auto_approve))
        
        console.print("\n[bold]Implementation Results:[/bold]")
        for result in results:
            console.print(f"✅ {result}")
            
    except Exception as e:
        logger.error(f"Error implementing changes: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('project_path', default='.')
@click.pass_context
def suggest_features(ctx, project_path):
    """Suggest new features and add-ons for the project."""
    console.print(f"[blue]Suggesting new features for: {project_path}[/blue]")
    
    try:
        agent = GenesisAgent()
        features = asyncio.run(agent.suggest_new_features(project_path))
        
        console.print("\n[bold]🚀 New Feature Suggestions:[/bold]")
        for feature in features:
            console.print(f"  {feature}")
            
    except Exception as e:
        logger.error(f"Error suggesting features: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('query')
@click.option('--language', help='Programming language filter')
@click.pass_context
def search_external(ctx, query, language):
    """Search external sources for code examples and implementations."""
    console.print(f"[blue]Searching external sources for: {query}[/blue]")
    
    try:
        agent = GenesisAgent()
        results = asyncio.run(agent.search_external_examples(query, language))
        
        console.print("\n[bold]🔍 External Search Results:[/bold]")
        for result in results:
            console.print(result)
            
    except Exception as e:
        logger.error(f"Error searching external sources: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('persona_name', required=False)
@click.option('--list', 'list_personas', is_flag=True, help='List available personas')
@click.option('--status', is_flag=True, help='Show current persona status')
@click.pass_context
def persona(ctx, persona_name, list_personas, status):
    """Manage AI agent personas."""
    try:
        agent = GenesisAgent()
        
        if list_personas:
            personas = asyncio.run(agent.get_available_personas())
            console.print("\n[bold]👤 Available Personas:[/bold]")
            for persona in personas:
                console.print(f"  {persona}")
        elif status:
            persona_status = asyncio.run(agent.get_persona_status())
            console.print(f"\n[bold]Current Persona:[/bold]\n{persona_status}")
        elif persona_name:
            result = asyncio.run(agent.set_persona(persona_name))
            console.print(result)
        else:
            console.print("Use --list to see available personas or specify a persona name")
            
    except Exception as e:
        logger.error(f"Error managing persona: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")


@cli.command()
@click.argument('category')
@click.argument('project_path', default='.')
@click.pass_context
def suggest_category_features(ctx, category, project_path):
    """Suggest features for a specific category (security, performance, ui, testing, etc.)."""
    console.print(f"[blue]Suggesting {category} features for: {project_path}[/blue]")
    
    try:
        agent = GenesisAgent()
        features = asyncio.run(agent.suggest_features_by_category(category, project_path))
        
        console.print(f"\n[bold]🔧 {category.title()} Feature Suggestions:[/bold]")
        for feature in features:
            console.print(f"  {feature}")
            
    except Exception as e:
        logger.error(f"Error suggesting {category} features: {e}")
        console.print(f"[red]Error: {e}[/red]")


async def run_interactive_session(agent: GenesisAgent):
    """Run the interactive session with the AI agent."""
    commands = {
        'help': 'Show available commands',
        'analyze': 'Analyze current directory',
        'suggest': 'Get improvement suggestions',
        'features': 'Suggest new features for the project',
        'search': 'Search external sources for examples',
        'persona': 'Manage AI agent personas',
        'implement': 'Implement suggested changes',
        'status': 'Show agent status',
        'learn': 'Enter learning mode',
        'quit': 'Exit the assistant'
    }
    
    console.print("[dim]💡 Tip: You can use natural language! Try saying 'suggest improvements' or 'analyze the code'[/dim]")
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]Genesis>[/bold cyan]").strip()
            
            if not user_input:
                continue
                
            command = user_input.lower()
            
            if command == 'quit' or command == 'exit':
                break
            elif command == 'help':
                console.print("\n[bold]Available Commands:[/bold]")
                for cmd, desc in commands.items():
                    console.print(f"  [cyan]{cmd}[/cyan] - {desc}")
                console.print("\n[dim]💡 You can also use natural language like 'suggest improvements' or 'implement changes'[/dim]")
            elif command == 'analyze':
                await handle_analyze_command(agent)
            elif command == 'suggest':
                await handle_suggest_command(agent)
            elif command == 'implement':
                await handle_implement_command(agent)
            elif command == 'status':
                await handle_status_command(agent)
            elif command == 'learn':
                await handle_learn_command(agent)
            elif command == 'features':
                await handle_features_command(agent)
            elif command == 'search':
                await handle_search_command(agent)
            elif command == 'persona':
                await handle_persona_command(agent)
            else:
                # Handle natural language input - check if it's an actionable command
                await handle_natural_language_input(agent, user_input)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error in interactive session: {e}")
            console.print(f"[red]Error: {e}[/red]")


async def handle_natural_language_input(agent: GenesisAgent, user_input: str):
    """Handle natural language input and route to appropriate handlers."""
    from core.agent import GenesisAgent
    
    # Parse the intent to see if we should execute a command directly
    intent = await agent._parse_intent(user_input)
    
    if intent['action'] == 'analyze':
        await handle_analyze_command(agent)
    elif intent['action'] == 'suggest':
        await handle_suggest_command(agent)
    elif intent['action'] == 'implement':
        await handle_implement_command(agent)
    elif intent['action'] == 'status':
        await handle_status_command(agent)
    elif intent['action'] == 'help':
        console.print(agent._get_help_message())
    elif intent['action'] == 'suggest_features':
        await handle_features_command(agent)
    elif intent['action'] == 'search_external':
        query = intent.get('query', user_input)
        console.print(f"[blue]Searching external sources for: {query}[/blue]")
        results = await agent.search_external_examples(query)
        console.print("\n[bold]🔍 External Search Results:[/bold]")
        for result in results:
            console.print(result)
    elif intent['action'] in ['set_persona', 'list_personas', 'persona_status']:
        if intent['action'] == 'list_personas':
            personas = await agent.get_available_personas()
            console.print("\n[bold]👤 Available Personas:[/bold]")
            for persona in personas:
                console.print(f"  {persona}")
        elif intent['action'] == 'persona_status':
            status = await agent.get_persona_status()
            console.print(f"\n[bold]Current Persona:[/bold]\n{status}")
        elif intent['action'] == 'set_persona':
            persona_name = intent.get('persona')
            if persona_name:
                result = await agent.set_persona(persona_name)
                console.print(result)
            else:
                console.print("Please specify a persona name")
    else:
        # For other intents, use the natural language processor
        response = await agent.process_natural_language(user_input)
        console.print(f"\n[green]Genesis:[/green] {response}")


async def handle_analyze_command(agent):
    """Handle the analyze command."""
    console.print("[blue]Analyzing current directory...[/blue]")
    results = await agent.analyze_code(".")
    for result in results:
        console.print(f"• {result}")


async def handle_suggest_command(agent):
    """Handle the suggest command."""
    console.print("[blue]Generating improvement suggestions...[/blue]")
    suggestions = await agent.suggest_improvements()
    
    if not suggestions or (len(suggestions) == 1 and "Error" in suggestions[0]):
        console.print("[yellow]No suggestions available or an error occurred.[/yellow]")
        return
    
    console.print("\n[bold]💡 Improvement Suggestions:[/bold]")
    for i, suggestion in enumerate(suggestions, 1):
        console.print(f"{i}. {suggestion}")
    
    # Ask if user wants to implement the suggestions
    console.print("\n")
    apply_suggestions = Prompt.ask(
        "[bold cyan]Would you like me to apply these suggestions?[/bold cyan]", 
        choices=['y', 'yes', 'n', 'no'], 
        default='n'
    )
    
    if apply_suggestions.lower() in ['y', 'yes']:
        console.print("[blue]Implementing suggested changes...[/blue]")
        results = await agent.implement_changes()
        if results:
            console.print("\n[bold]✅ Implementation Results:[/bold]")
            for result in results:
                console.print(f"  • {result}")
        else:
            console.print("[yellow]No changes were implemented.[/yellow]")
    else:
        console.print("[dim]You can run '[cyan]implement[/cyan]' later to apply these suggestions.[/dim]")


async def handle_implement_command(agent):
    """Handle the implement command."""
    confirm = Prompt.ask("Are you sure you want to implement changes?", choices=['y', 'n'], default='n')
    if confirm == 'y':
        console.print("[blue]Implementing changes...[/blue]")
        results = await agent.implement_changes()
        for result in results:
            console.print(f"✅ {result}")


async def handle_status_command(agent):
    """Handle the status command."""
    status = await agent.get_status()
    console.print(f"\n[bold]Agent Status:[/bold]")
    console.print(f"Mode: {status['mode']}")
    console.print(f"Active: {status['active']}")
    console.print(f"Learning: {status['learning_enabled']}")


async def handle_learn_command(agent):
    """Handle the learn command."""
    console.print("[blue]Entering learning mode...[/blue]")
    feedback = Prompt.ask("What would you like me to learn from?")
    await agent.learn_from_feedback(feedback)
    console.print("[green]Thank you for the feedback! I'll use this to improve.[/green]")


async def handle_features_command(agent):
    """Handle the features command."""
    console.print("[blue]Generating new feature suggestions...[/blue]")
    features = await agent.suggest_new_features()
    
    if not features or (len(features) == 1 and "Error" in features[0]):
        console.print("[yellow]No feature suggestions available or an error occurred.[/yellow]")
        return
    
    console.print("\n[bold]🚀 New Feature Suggestions:[/bold]")
    for feature in features:
        console.print(f"  {feature}")


async def handle_search_command(agent):
    """Handle the search command."""
    query = Prompt.ask("[cyan]What would you like to search for?[/cyan]")
    if not query:
        return
    
    console.print(f"[blue]Searching external sources for: {query}[/blue]")
    results = await agent.search_external_examples(query)
    
    console.print("\n[bold]🔍 External Search Results:[/bold]")
    for result in results:
        console.print(result)


async def handle_persona_command(agent):
    """Handle the persona command."""
    action = Prompt.ask(
        "[cyan]What would you like to do?[/cyan]",
        choices=['list', 'status', 'set'],
        default='list'
    )
    
    if action == 'list':
        personas = await agent.get_available_personas()
        console.print("\n[bold]👤 Available Personas:[/bold]")
        for persona in personas:
            console.print(f"  {persona}")
    elif action == 'status':
        status = await agent.get_persona_status()
        console.print(f"\n[bold]Current Persona:[/bold]\n{status}")
    elif action == 'set':
        persona_name = Prompt.ask("[cyan]Enter persona name[/cyan]")
        if persona_name:
            result = await agent.set_persona(persona_name)
            console.print(result)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Default to interactive mode if no arguments
        sys.argv.append('interactive')
    cli()