"""Feature installation system for Genesis AI Agent."""

import os
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict

from rich.console import Console
from rich.prompt import Confirm, Prompt, IntPrompt
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from fuzzywuzzy import fuzz, process

from core.config import Config
from utils.logger import get_logger
from feature_suggester.suggester import FeatureSuggestion


@dataclass
class FeatureTemplate:
    """Represents a feature template for installation."""
    name: str
    description: str
    category: str
    files: Dict[str, str]  # relative_path -> template_content
    dependencies: List[str]
    requirements: List[str]  # Python packages
    post_install_steps: List[str]
    version: str = "1.0.0"


@dataclass
class InstallationRecord:
    """Records an installation for potential rollback."""
    feature_name: str
    timestamp: str
    files_created: List[str]
    files_modified: List[str]
    dependencies_added: List[str]
    backup_paths: List[str]
    success: bool = True


class FeatureInstaller:
    """Handles feature installation with backup and rollback capabilities."""
    
    def __init__(self, config: Config):
        """Initialize the feature installer."""
        self.config = config
        self.logger = get_logger(__name__)
        self.console = Console()
        
        # Paths
        self.templates_dir = Path(__file__).parent / "templates"
        self.backups_dir = Path(__file__).parent / "backups"
        self.install_log = Path(".genesis_installations.json")
        
        # Ensure directories exist
        self.templates_dir.mkdir(exist_ok=True)
        self.backups_dir.mkdir(exist_ok=True)
        
        self.logger.info("Feature installer initialized")
    
    def get_available_features(self) -> List[str]:
        """Get list of available features for installation."""
        features = []
        if self.templates_dir.exists():
            for template_dir in self.templates_dir.iterdir():
                if template_dir.is_dir() and (template_dir / "feature.json").exists():
                    features.append(template_dir.name)
        return sorted(features)
    
    def get_feature_info(self, feature_name: str) -> Optional[FeatureTemplate]:
        """Get detailed information about a feature."""
        feature_dir = self.templates_dir / feature_name
        feature_file = feature_dir / "feature.json"
        
        if not feature_file.exists():
            return None
        
        try:
            with feature_file.open() as f:
                data = json.load(f)
            
            # Load file templates
            files = {}
            files_dir = feature_dir / "files"
            if files_dir.exists():
                for file_path in files_dir.rglob("*"):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(files_dir)
                        with file_path.open() as f:
                            files[str(rel_path)] = f.read()
            
            return FeatureTemplate(
                name=data["name"],
                description=data["description"],
                category=data["category"],
                files=files,
                dependencies=data.get("dependencies", []),
                requirements=data.get("requirements", []),
                post_install_steps=data.get("post_install_steps", []),
                version=data.get("version", "1.0.0")
            )
        except Exception as e:
            self.logger.error(f"Error loading feature {feature_name}: {e}")
            return None
    
    def preview_feature(self, feature_name: str) -> None:
        """Display detailed preview of a feature."""
        feature = self.get_feature_info(feature_name)
        if not feature:
            self.console.print(f"[red]Feature '{feature_name}' not found[/red]")
            return
        
        # Create a rich panel for the feature preview
        content = []
        content.append(f"[dim]{feature.description}[/dim]")
        content.append(f"Category: [cyan]{feature.category}[/cyan] | Version: [green]{feature.version}[/green]")
        
        if feature.files:
            content.append("\n[bold]Files to be created/modified:[/bold]")
            for file_path in feature.files.keys():
                content.append(f"  📄 [blue]{file_path}[/blue]")
        
        if feature.requirements:
            content.append("\n[bold]Python dependencies:[/bold]")
            for req in feature.requirements:
                content.append(f"  📦 [yellow]{req}[/yellow]")
        
        if feature.post_install_steps:
            content.append("\n[bold]Post-installation steps:[/bold]")
            for i, step in enumerate(feature.post_install_steps, 1):
                content.append(f"  {i}. [dim]{step}[/dim]")
        
        panel = Panel(
            "\n".join(content),
            title=f"📦 {feature.name}",
            title_align="left",
            border_style="blue"
        )
        
        self.console.print(panel)
    
    def fuzzy_search_features(self, query: str, limit: int = 5) -> List[str]:
        """Search for features using fuzzy matching."""
        available = self.get_available_features()
        if not available:
            return []
        
        # Create search candidates with both name and description
        candidates = {}
        for feature_name in available:
            feature_info = self.get_feature_info(feature_name)
            if feature_info:
                candidates[feature_name] = f"{feature_info.name} {feature_info.description} {feature_info.category}"
        
        # Perform fuzzy search
        matches = process.extract(query, candidates, limit=limit, scorer=fuzz.partial_ratio)
        return [match[0] for match in matches if match[1] > 60]  # Only return matches above 60% similarity
    
    def interactive_feature_selection(self) -> Optional[str]:
        """Interactive feature selection with search and preview."""
        available = self.get_available_features()
        if not available:
            self.console.print("[yellow]No features available for installation[/yellow]")
            return None
        
        while True:
            self.console.print("\n[bold blue]📦 Feature Installation[/bold blue]")
            
            # Display available features in a nice table
            table = Table(title="Available Features")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Description", style="white")
            table.add_column("Category", style="green")
            
            for feature_name in available:
                feature_info = self.get_feature_info(feature_name)
                if feature_info:
                    table.add_row(
                        feature_name,
                        feature_info.description[:60] + "..." if len(feature_info.description) > 60 else feature_info.description,
                        feature_info.category
                    )
            
            self.console.print(table)
            
            # Get user input
            user_input = Prompt.ask(
                "\n[cyan]Enter feature name, search query, or command[/cyan]",
                default="help"
            ).strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                return None
            elif user_input.lower() == 'help':
                self.console.print("\n[bold]Commands:[/bold]")
                self.console.print("  • Enter feature name to install")
                self.console.print("  • Type search query to find features")
                self.console.print("  • 'preview <feature>' to preview before installing")
                self.console.print("  • 'quit' to exit")
                continue
            elif user_input.lower().startswith('preview '):
                feature_name = user_input[8:].strip()
                self.preview_feature(feature_name)
                continue
            
            # Check if it's an exact match
            if user_input in available:
                return user_input
            
            # Try fuzzy search
            matches = self.fuzzy_search_features(user_input)
            if matches:
                if len(matches) == 1:
                    self.console.print(f"[green]Found match: {matches[0]}[/green]")
                    return matches[0]
                else:
                    self.console.print(f"\n[yellow]Found {len(matches)} similar features:[/yellow]")
                    for i, match in enumerate(matches, 1):
                        feature_info = self.get_feature_info(match)
                        self.console.print(f"  {i}. [cyan]{match}[/cyan] - {feature_info.description if feature_info else 'No description'}")
                    
                    try:
                        choice = IntPrompt.ask(
                            f"Select feature (1-{len(matches)}) or 0 to search again",
                            default=0
                        )
                        if 1 <= choice <= len(matches):
                            return matches[choice - 1]
                    except (ValueError, KeyboardInterrupt):
                        continue
            else:
                self.console.print(f"[red]No features found matching '{user_input}'[/red]")
                continue
    
    async def install_feature(self, feature_name: str, auto_approve: bool = False, 
                            target_dir: str = ".") -> bool:
        """Install a feature with backup and confirmation."""
        feature = self.get_feature_info(feature_name)
        if not feature:
            self.console.print(f"[red]Feature '{feature_name}' not found[/red]")
            return False
        
        target_path = Path(target_dir).resolve()
        self.console.print(f"\n[bold blue]Installing {feature.name}[/bold blue]")
        
        # Check for conflicts
        conflicts = self._check_conflicts(feature, target_path)
        if conflicts and not auto_approve:
            self.console.print("\n[yellow]⚠️  The following files will be overwritten:[/yellow]")
            for conflict in conflicts:
                self.console.print(f"  📄 {conflict}")
            
            if not Confirm.ask("\nContinue with installation?"):
                self.console.print("[yellow]Installation cancelled[/yellow]")
                return False
        
        # Create installation record
        record = InstallationRecord(
            feature_name=feature.name,
            timestamp=datetime.now().isoformat(),
            files_created=[],
            files_modified=[],
            dependencies_added=[],
            backup_paths=[]
        )
        
        try:
            with Progress() as progress:
                task = progress.add_task(f"Installing {feature.name}...", total=100)
                
                # Create backups
                await self._create_backups(conflicts, record, target_path)
                progress.update(task, advance=20)
                
                # Install files
                await self._install_files(feature, record, target_path)
                progress.update(task, advance=40)
                
                # Install Python dependencies
                await self._install_requirements(feature, record)
                progress.update(task, advance=30)
                
                # Run post-install steps
                await self._run_post_install_steps(feature)
                progress.update(task, advance=10)
            
            # Save installation record
            self._save_installation_record(record)
            
            self.console.print(f"\n[green]✅ Successfully installed {feature.name}[/green]")
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing {feature_name}: {e}")
            self.console.print(f"[red]❌ Installation failed: {e}[/red]")
            
            # Attempt rollback
            try:
                await self._rollback_installation(record)
                self.console.print("[yellow]🔄 Changes rolled back[/yellow]")
            except Exception as rollback_error:
                self.logger.error(f"Rollback failed: {rollback_error}")
                self.console.print(f"[red]⚠️  Rollback failed: {rollback_error}[/red]")
            
            return False
    
    async def install_multiple_features(self, feature_names: List[str], 
                                      auto_approve: bool = False) -> Dict[str, bool]:
        """Install multiple features in batch."""
        results = {}
        
        self.console.print(f"\n[bold blue]📦 Batch installing {len(feature_names)} features[/bold blue]")
        
        for feature_name in feature_names:
            self.console.print(f"\n[dim]--- Installing {feature_name} ---[/dim]")
            results[feature_name] = await self.install_feature(
                feature_name, auto_approve=auto_approve
            )
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        self.console.print(f"\n[bold]Installation Summary:[/bold]")
        self.console.print(f"✅ Successful: {successful}")
        self.console.print(f"❌ Failed: {len(feature_names) - successful}")
        
        return results
    
    def list_installations(self) -> List[InstallationRecord]:
        """List all previous installations."""
        if not self.install_log.exists():
            return []
        
        try:
            with self.install_log.open() as f:
                data = json.load(f)
            return [InstallationRecord(**record) for record in data]
        except Exception as e:
            self.logger.error(f"Error reading installation log: {e}")
            return []
    
    async def rollback_installation(self, feature_name: str) -> bool:
        """Rollback a specific installation."""
        installations = self.list_installations()
        
        # Find the most recent installation of this feature
        target_record = None
        for record in reversed(installations):
            if record.feature_name == feature_name:
                target_record = record
                break
        
        if not target_record:
            self.console.print(f"[red]No installation record found for {feature_name}[/red]")
            return False
        
        try:
            await self._rollback_installation(target_record)
            self.console.print(f"[green]✅ Successfully rolled back {feature_name}[/green]")
            return True
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            self.console.print(f"[red]❌ Rollback failed: {e}[/red]")
            return False
    
    def _check_conflicts(self, feature: FeatureTemplate, target_path: Path) -> List[str]:
        """Check for file conflicts before installation."""
        conflicts = []
        for file_path in feature.files.keys():
            full_path = target_path / file_path
            if full_path.exists():
                conflicts.append(str(file_path))
        return conflicts
    
    async def _create_backups(self, conflicts: List[str], record: InstallationRecord, 
                            target_path: Path) -> None:
        """Create backups of existing files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for conflict in conflicts:
            source = target_path / conflict
            backup_name = f"{record.feature_name}_{timestamp}_{conflict.replace('/', '_')}"
            backup_path = self.backups_dir / backup_name
            
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, backup_path)
            record.backup_paths.append(str(backup_path))
            record.files_modified.append(conflict)
    
    async def _install_files(self, feature: FeatureTemplate, record: InstallationRecord,
                           target_path: Path) -> None:
        """Install feature files."""
        for file_path, content in feature.files.items():
            full_path = target_path / file_path
            
            # Ensure directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content
            with full_path.open('w') as f:
                f.write(content)
            
            if str(file_path) not in record.files_modified:
                record.files_created.append(str(file_path))
    
    async def _install_requirements(self, feature: FeatureTemplate, 
                                  record: InstallationRecord) -> None:
        """Install Python requirements."""
        if not feature.requirements:
            return
        
        # Update requirements.txt
        requirements_file = Path("requirements.txt")
        existing_reqs = set()
        
        if requirements_file.exists():
            with requirements_file.open() as f:
                existing_reqs = {line.strip() for line in f if line.strip() and not line.startswith('#')}
        
        new_reqs = []
        for req in feature.requirements:
            if req not in existing_reqs:
                new_reqs.append(req)
                record.dependencies_added.append(req)
        
        if new_reqs:
            with requirements_file.open('a') as f:
                f.write(f"\n# Added by {feature.name} feature\n")
                for req in new_reqs:
                    f.write(f"{req}\n")
            
            # Install packages
            try:
                subprocess.run([
                    "pip", "install", "--user", *new_reqs
                ], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                raise Exception(f"Failed to install Python packages: {e}")
    
    async def _run_post_install_steps(self, feature: FeatureTemplate) -> None:
        """Run post-installation steps."""
        for step in feature.post_install_steps:
            self.console.print(f"[dim]Running: {step}[/dim]")
            # For now, just display the steps. In a real implementation,
            # you might want to execute shell commands or Python code.
    
    async def _rollback_installation(self, record: InstallationRecord) -> None:
        """Rollback an installation using the record."""
        # Remove created files
        for file_path in record.files_created:
            full_path = Path(file_path)
            if full_path.exists():
                full_path.unlink()
        
        # Restore backed up files
        for backup_path in record.backup_paths:
            backup = Path(backup_path)
            if backup.exists():
                # Extract original path from backup name
                # This is a simplified approach - in production you'd want more robust mapping
                pass  # Implementation would restore from backup
        
        # Remove dependencies from requirements.txt
        if record.dependencies_added:
            requirements_file = Path("requirements.txt")
            if requirements_file.exists():
                with requirements_file.open() as f:
                    lines = f.readlines()
                
                # Remove the added dependencies
                filtered_lines = []
                for line in lines:
                    if line.strip() not in record.dependencies_added:
                        filtered_lines.append(line)
                
                with requirements_file.open('w') as f:
                    f.writelines(filtered_lines)
    
    def _save_installation_record(self, record: InstallationRecord) -> None:
        """Save installation record to log file."""
        records = []
        if self.install_log.exists():
            try:
                with self.install_log.open() as f:
                    records = json.load(f)
            except Exception as e:
                self.logger.error(f"Error reading installation log: {e}")
        
        records.append(asdict(record))
        
        with self.install_log.open('w') as f:
            json.dump(records, f, indent=2)