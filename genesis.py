#!/usr/bin/env python3
"""
Genesis AI Coding Agent
A fully functional self-improving AI virtual assistant coding agent.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from dotenv import load_dotenv

from core.agent import GenesisAgent
from core.config import Config
from utils.logger import setup_logger
from features.installer import FeatureInstaller

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
@click.option('--interactive', is_flag=True, help='Enable interactive selection of features')
@click.pass_context
def suggest_features(ctx, project_path, interactive):
    """Suggest new features and add-ons for the project."""
    console.print(f"[blue]Suggesting new features for: {project_path}[/blue]")
    
    try:
        agent = GenesisAgent()
        features = asyncio.run(agent.suggest_new_features(project_path))
        
        if not features or (len(features) == 1 and "Error" in str(features[0])):
            console.print("[yellow]No feature suggestions available or an error occurred.[/yellow]")
            if "GITHUB_TOKEN" in str(features[0]) if features else False:
                console.print("[dim]Note: Some features require GITHUB_TOKEN for enhanced suggestions[/dim]")
            return
        
        console.print("\n[bold]🚀 New Feature Suggestions:[/bold]")
        numbered_features = []
        for i, feature in enumerate(features, 1):
            console.print(f"  [cyan]{i}.[/cyan] {feature}")
            numbered_features.append((i, feature))
        
        if interactive and numbered_features:
            console.print("\n[dim]You can select features to implement by number (e.g., '1,3,5' or 'all')[/dim]")
            selection = Prompt.ask(
                "[bold cyan]Select features to implement (or 'none' to skip)[/bold cyan]",
                default="none"
            )
            
            if selection.lower() not in ['none', 'skip', '']:
                selected_indices = []
                if selection.lower() == 'all':
                    selected_indices = list(range(1, len(numbered_features) + 1))
                else:
                    try:
                        selected_indices = [int(x.strip()) for x in selection.split(',')]
                    except ValueError:
                        console.print("[red]Invalid selection format. Use numbers separated by commas.[/red]")
                        return
                
                # Validate indices
                valid_indices = [i for i in selected_indices if 1 <= i <= len(numbered_features)]
                if valid_indices:
                    console.print(f"\n[blue]Selected features: {', '.join(map(str, valid_indices))}[/blue]")
                    for idx in valid_indices:
                        feature = numbered_features[idx-1][1]
                        console.print(f"[green]Would implement:[/green] {feature}")
                    
                    confirm = Confirm.ask("\nProceed with implementation?", default=False)
                    if confirm:
                        console.print("[blue]Implementation would begin here...[/blue]")
                        console.print("[yellow]Note: Feature implementation is a placeholder for now[/yellow]")
                else:
                    console.print("[red]No valid feature numbers selected.[/red]")
        elif not interactive:
            console.print("\n[dim]Use --interactive to select and implement features by number[/dim]")
            
    except Exception as e:
        logger.error(f"Error suggesting features: {e}")
        console.print(f"[red]Error: {e}[/red]")
        if "GITHUB_TOKEN" in str(e):
            console.print("[dim]Tip: Set GITHUB_TOKEN environment variable for enhanced suggestions[/dim]")


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


# Feature Installation Commands

@cli.command('install-feature')
@click.argument('feature_names', nargs=-1, required=True)
@click.option('--auto-approve', is_flag=True, help='Auto-approve all changes without prompts')
@click.option('--list-available', is_flag=True, help='List all available features')
@click.option('--preview', is_flag=True, help='Preview the feature without installing')
@click.option('--target-dir', default='.', help='Target directory for installation')
@click.pass_context  
def install_feature(ctx, feature_names, auto_approve, list_available, preview, target_dir):
    """Install one or more features into your project."""
    try:
        config = Config()
        installer = FeatureInstaller(config)
        
        if list_available:
            available = installer.get_available_features()
            if available:
                console.print("\n[bold blue]📦 Available Features:[/bold blue]")
                for feature_name in available:
                    feature_info = installer.get_feature_info(feature_name)
                    if feature_info:
                        console.print(f"  [cyan]{feature_name}[/cyan] - {feature_info.description}")
            else:
                console.print("[yellow]No features available for installation[/yellow]")
            return
        
        if not feature_names:
            console.print("[red]Please specify feature name(s) to install[/red]")
            return
        
        for feature_name in feature_names:
            if preview:
                installer.preview_feature(feature_name)
            else:
                console.print(f"\n[bold blue]Installing feature: {feature_name}[/bold blue]")
                success = asyncio.run(installer.install_feature(
                    feature_name, 
                    auto_approve=auto_approve,
                    target_dir=target_dir
                ))
                
                if not success:
                    console.print(f"[red]Failed to install {feature_name}[/red]")
                    
    except Exception as e:
        logger.error(f"Error with feature installation: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command('list-features')
@click.option('--installed', is_flag=True, help='Show installed features')
@click.pass_context
def list_features(ctx, installed):
    """List available or installed features."""
    try:
        config = Config()
        installer = FeatureInstaller(config)
        
        if installed:
            installations = installer.list_installations()
            if installations:
                console.print("\n[bold green]📦 Installed Features:[/bold green]")
                
                table = Table()
                table.add_column("Feature", style="cyan")
                table.add_column("Installed", style="green")
                table.add_column("Status", style="yellow")
                
                for record in installations:
                    status = "✅ Success" if record.success else "❌ Failed"
                    table.add_row(record.feature_name, record.timestamp[:19], status)
                
                console.print(table)
            else:
                console.print("[yellow]No features installed yet[/yellow]")
        else:
            available = installer.get_available_features()
            if available:
                console.print("\n[bold blue]📦 Available Features:[/bold blue]")
                for feature_name in available:
                    feature_info = installer.get_feature_info(feature_name)
                    if feature_info:
                        console.print(f"  [cyan]{feature_name}[/cyan] - {feature_info.description}")
                        console.print(f"    Category: {feature_info.category} | Version: {feature_info.version}")
            else:
                console.print("[yellow]No features available for installation[/yellow]")
                
    except Exception as e:
        logger.error(f"Error listing features: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command('preview-feature')
@click.argument('feature_name')
@click.pass_context
def preview_feature(ctx, feature_name):
    """Preview a feature before installation."""
    try:
        config = Config()
        installer = FeatureInstaller(config)
        installer.preview_feature(feature_name)
        
    except Exception as e:
        logger.error(f"Error previewing feature: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command('rollback-feature')
@click.argument('feature_name')
@click.pass_context
def rollback_feature(ctx, feature_name):
    """Rollback a previously installed feature."""
    try:
        config = Config()
        installer = FeatureInstaller(config)
        
        console.print(f"[yellow]Rolling back feature: {feature_name}[/yellow]")
        success = asyncio.run(installer.rollback_installation(feature_name))
        
        if success:
            console.print(f"[green]✅ Successfully rolled back {feature_name}[/green]")
        else:
            console.print(f"[red]❌ Failed to rollback {feature_name}[/red]")
            
    except Exception as e:
        logger.error(f"Error rolling back feature: {e}")
        console.print(f"[red]Error: {e}[/red]")


# Enhanced Persona Management Commands

@cli.command('create-persona')
@click.option('--interactive', is_flag=True, help='Use guided creation process')
@click.pass_context
def create_persona(ctx, interactive):
    """Create a new custom persona."""
    try:
        config = Config()
        from personas.persona_manager import PersonaManager
        persona_manager = PersonaManager(config)
        
        if interactive:
            # Guided persona creation
            console.print("\n[bold blue]🎭 Creating New Persona[/bold blue]")
            console.print("[dim]Let's create a custom AI persona tailored to your needs![/dim]")
            
            # Show examples for inspiration
            console.print("\n[bold]💡 Examples of personas you might create:[/bold]")
            examples = [
                "Frontend Developer - Specializes in React, CSS, and UX design",
                "Security Expert - Focuses on security vulnerabilities and best practices", 
                "Performance Optimizer - Emphasizes speed, efficiency, and scalability",
                "DevOps Engineer - Concentrates on deployment, CI/CD, and infrastructure",
                "Junior Mentor - Patient and educational approach for learning"
            ]
            for example in examples:
                console.print(f"  [dim]• {example}[/dim]")
            
            console.print("\n" + "="*60)
            
            name = Prompt.ask("[cyan]What would you like to name your persona?[/cyan]")
            
            description = Prompt.ask(
                "[cyan]Briefly describe this persona (what they specialize in)[/cyan]",
                default=f"A specialized AI assistant focused on {name.lower()}"
            )
            
            console.print(f"\n[dim]📚 Enter expertise areas for {name} (one per line, empty line to finish):[/dim]")
            console.print("[dim]Examples: python, web development, testing, security, etc.[/dim]")
            expertise_areas = []
            while True:
                area = input("  > ").strip()
                if not area:
                    break
                expertise_areas.append(area)
            
            if not expertise_areas:
                expertise_areas = ["general programming", "code analysis"]
                console.print("[dim]No expertise areas provided, using defaults[/dim]")
            
            communication_style = Prompt.ask(
                "[cyan]Communication style[/cyan]",
                choices=["professional", "casual", "technical", "encouraging", "formal"],
                default="professional"
            )
            
            # Show preview
            console.print(f"\n[bold]📋 Persona Preview:[/bold]")
            console.print(f"[cyan]Name:[/cyan] {name}")
            console.print(f"[cyan]Description:[/cyan] {description}")
            console.print(f"[cyan]Expertise:[/cyan] {', '.join(expertise_areas)}")
            console.print(f"[cyan]Style:[/cyan] {communication_style}")
            
            if not Confirm.ask("\nCreate this persona?", default=True):
                console.print("[yellow]Persona creation cancelled[/yellow]")
                return
            
            # Create the persona
            persona_data = {
                "name": name,
                "description": description,
                "expertise_areas": expertise_areas,
                "communication_style": communication_style,
                "custom": True
            }
            
            success = persona_manager.create_custom_persona(name, persona_data)
            if success:
                console.print(f"[green]✅ Created persona: {name}[/green]")
                console.print(f"[dim]💡 Use 'python genesis.py persona {name}' to activate it[/dim]")
            else:
                console.print(f"[red]❌ Failed to create persona[/red]")
        else:
            console.print("[yellow]Use --interactive for guided persona creation[/yellow]")
            console.print("[dim]Example: python genesis.py create-persona --interactive[/dim]")
            
    except Exception as e:
        logger.error(f"Error creating persona: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command('export-persona')
@click.argument('persona_name')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def export_persona(ctx, persona_name, output):
    """Export a persona to a file for sharing."""
    try:
        config = Config()
        from personas.persona_manager import PersonaManager
        persona_manager = PersonaManager(config)
        
        persona_info = persona_manager.get_persona_info(persona_name)
        if not persona_info:
            console.print(f"[red]Persona '{persona_name}' not found[/red]")
            return
        
        import json
        output_file = output or f"{persona_name.lower().replace(' ', '_')}_persona.json"
        
        with open(output_file, 'w') as f:
            json.dump(persona_info, f, indent=2)
        
        console.print(f"[green]✅ Exported persona to: {output_file}[/green]")
        
    except Exception as e:
        logger.error(f"Error exporting persona: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command('import-persona')
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def import_persona(ctx, file_path):
    """Import a persona from a file."""
    try:
        config = Config()
        from personas.persona_manager import PersonaManager
        persona_manager = PersonaManager(config)
        
        import json
        with open(file_path) as f:
            persona_data = json.load(f)
        
        name = persona_data.get('name')
        if not name:
            console.print("[red]Invalid persona file: missing name[/red]")
            return
        
        success = persona_manager.create_custom_persona(name, persona_data)
        if success:
            console.print(f"[green]✅ Imported persona: {name}[/green]")
        else:
            console.print(f"[red]❌ Failed to import persona[/red]")
            
    except Exception as e:
        logger.error(f"Error importing persona: {e}")
        console.print(f"[red]Error: {e}[/red]")


@cli.command('serve')
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=5000, help='Port to listen on')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def serve(ctx, host, port, debug):
    """Start the Genesis web API server."""
    console.print(f"[bold blue]🌐 Starting Genesis Web API Server[/bold blue]")
    console.print(f"Server will be available at: http://{host}:{port}")
    console.print("Press Ctrl+C to stop the server")
    
    try:
        from api.app import run_web_server
        run_web_server(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
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
        'install': 'Install available features',
        'list-features': 'List available/installed features',
        'serve': 'Start web API server',
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
            elif command == 'install':
                await handle_install_command()
            elif command == 'list-features':
                await handle_list_features_command()
            elif command == 'serve':
                await handle_serve_command()
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
    
    if not features or (len(features) == 1 and "Error" in str(features[0])):
        console.print("[yellow]No feature suggestions available or an error occurred.[/yellow]")
        if features and "GITHUB_TOKEN" in str(features[0]):
            console.print("[dim]Note: Some features require GITHUB_TOKEN for enhanced suggestions[/dim]")
        return
    
    console.print("\n[bold]🚀 New Feature Suggestions:[/bold]")
    numbered_features = []
    for i, feature in enumerate(features, 1):
        console.print(f"  [cyan]{i}.[/cyan] {feature}")
        numbered_features.append((i, feature))
    
    if numbered_features:
        console.print("\n[dim]💡 Tip: You can select features by number (e.g., '1,3,5' or 'all')[/dim]")
        selection = Prompt.ask(
            "[bold cyan]Select features to implement (or 'none' to skip)[/bold cyan]",
            default="none"
        )
        
        if selection.lower() not in ['none', 'skip', '']:
            selected_indices = []
            if selection.lower() == 'all':
                selected_indices = list(range(1, len(numbered_features) + 1))
            else:
                try:
                    selected_indices = [int(x.strip()) for x in selection.split(',')]
                except ValueError:
                    console.print("[red]Invalid selection format. Use numbers separated by commas.[/red]")
                    return
            
            # Validate indices
            valid_indices = [i for i in selected_indices if 1 <= i <= len(numbered_features)]
            if valid_indices:
                console.print(f"\n[blue]Selected features: {', '.join(map(str, valid_indices))}[/blue]")
                for idx in valid_indices:
                    feature = numbered_features[idx-1][1]
                    console.print(f"[green]Would implement:[/green] {feature}")
                
                confirm = Confirm.ask("\nProceed with implementation?", default=False)
                if confirm:
                    console.print("[blue]Implementation would begin here...[/blue]")
                    console.print("[yellow]Note: Feature implementation is a placeholder for now[/yellow]")
            else:
                console.print("[red]No valid feature numbers selected.[/red]")


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


async def handle_install_command():
    """Handle the install command for features."""
    try:
        config = Config()
        installer = FeatureInstaller(config)
        
        # Use interactive selection
        feature_name = installer.interactive_feature_selection()
        if not feature_name:
            console.print("[yellow]Installation cancelled[/yellow]")
            return
        
        # Preview before installation
        installer.preview_feature(feature_name)
        
        if not Confirm.ask(f"\nInstall {feature_name}?", default=True):
            console.print("[yellow]Installation cancelled[/yellow]")
            return
        
        # Install the feature
        success = await installer.install_feature(feature_name)
        if success:
            console.print(f"[green]✅ Successfully installed {feature_name}[/green]")
        else:
            console.print(f"[red]❌ Failed to install {feature_name}[/red]")
                
    except Exception as e:
        logger.error(f"Error in install command: {e}")
        console.print(f"[red]Error: {e}[/red]")


async def handle_list_features_command():
    """Handle the list-features command."""
    try:
        config = Config()
        installer = FeatureInstaller(config)
        
        action = Prompt.ask(
            "[cyan]What would you like to list?[/cyan]",
            choices=['available', 'installed'],
            default='available'
        )
        
        if action == 'available':
            available = installer.get_available_features()
            if available:
                console.print("\n[bold blue]📦 Available Features:[/bold blue]")
                for feature_name in available:
                    feature_info = installer.get_feature_info(feature_name)
                    if feature_info:
                        console.print(f"  [cyan]{feature_name}[/cyan] - {feature_info.description}")
                        console.print(f"    Category: {feature_info.category} | Version: {feature_info.version}")
            else:
                console.print("[yellow]No features available for installation[/yellow]")
        
        elif action == 'installed':
            installations = installer.list_installations()
            if installations:
                console.print("\n[bold green]📦 Installed Features:[/bold green]")
                
                for record in installations:
                    status = "✅ Success" if record.success else "❌ Failed"
                    console.print(f"  {status} [cyan]{record.feature_name}[/cyan] - {record.timestamp[:19]}")
            else:
                console.print("[yellow]No features installed yet[/yellow]")
                
    except Exception as e:
        logger.error(f"Error listing features: {e}")
        console.print(f"[red]Error: {e}[/red]")


async def handle_serve_command():
    """Handle the serve command to start web API."""
    try:
        console.print("[bold blue]🌐 Starting Genesis Web API Server...[/bold blue]")
        console.print("Server will be available at: http://127.0.0.1:5000")
        console.print("[dim]Press Ctrl+C to return to interactive mode[/dim]")
        
        from api.app import run_web_server
        run_web_server(host='127.0.0.1', port=5000, debug=False)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Web server stopped, returning to interactive mode[/yellow]")
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        console.print(f"[red]Error: {e}[/red]")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Default to interactive mode if no arguments
        sys.argv.append('interactive')
    cli()