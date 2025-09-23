"""Feature suggester for recommending new functionality and add-ons."""

import os
import ast
import json
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from core.config import Config
from utils.logger import get_logger
from external_search.search_client import ExternalSearchClient, SearchResult


@dataclass
class FeatureSuggestion:
    """Represents a feature suggestion."""
    name: str
    description: str
    category: str
    implementation_steps: List[str]
    files_to_create: List[str]
    files_to_modify: List[str]
    dependencies: List[str]
    examples: List[SearchResult]
    priority: str = "medium"  # low, medium, high
    confidence: float = 0.8
    estimated_effort: str = "medium"  # small, medium, large


class FeatureSuggester:
    """Suggests new features and add-ons based on project analysis and external sources."""
    
    def __init__(self, config: Config):
        """Initialize the feature suggester."""
        self.config = config
        self.logger = get_logger(__name__)
        self.search_client = ExternalSearchClient(config)
        
        # Feature templates for common patterns
        self.feature_templates = self._load_feature_templates()
        
        self.logger.info("Feature suggester initialized")
    
    async def suggest_features_for_project(self, project_path: str = ".") -> List[FeatureSuggestion]:
        """Analyze a project and suggest new features."""
        self.logger.info(f"Suggesting features for project: {project_path}")
        
        try:
            # Analyze project structure and code
            project_info = await self._analyze_project_structure(project_path)
            
            # Generate feature suggestions based on analysis
            suggestions = []
            
            # Rule-based suggestions (always available)
            rule_based = await self._generate_rule_based_suggestions(project_info)
            suggestions.extend(rule_based)
            
            # Template-based suggestions (always available)
            template_based = await self._generate_template_based_suggestions(project_info)
            suggestions.extend(template_based)
            
            # External search-based suggestions (may fail without tokens)
            try:
                search_based = await self._generate_search_based_suggestions(project_info)
                suggestions.extend(search_based)
            except Exception as search_error:
                self.logger.warning(f"External search unavailable: {search_error}")
                # Add fallback generic suggestions
                fallback_suggestions = self._get_fallback_suggestions(project_info)
                suggestions.extend(fallback_suggestions)
            
            # If we still don't have enough suggestions, add more fallbacks
            if len(suggestions) < 5:
                additional_fallbacks = self._get_additional_fallback_suggestions(project_info)
                suggestions.extend(additional_fallbacks)
            
            # Remove duplicates by name
            seen_names = set()
            unique_suggestions = []
            for suggestion in suggestions:
                if suggestion.name not in seen_names:
                    unique_suggestions.append(suggestion)
                    seen_names.add(suggestion.name)
            
            # Sort by priority and confidence
            unique_suggestions.sort(key=lambda x: (self._priority_score(x.priority), x.confidence), reverse=True)
            
            return unique_suggestions[:15]  # Return top 15 suggestions
            
        except Exception as e:
            self.logger.error(f"Error suggesting features: {e}")
            # Last resort fallback
            return self._get_basic_fallback_suggestions()
    
    async def suggest_features_by_category(self, category: str, project_path: str = ".") -> List[FeatureSuggestion]:
        """Suggest features for a specific category."""
        self.logger.info(f"Suggesting {category} features")
        
        all_suggestions = await self.suggest_features_for_project(project_path)
        return [s for s in all_suggestions if s.category.lower() == category.lower()]
    
    async def search_and_suggest_similar_features(self, description: str, language: str = None) -> List[FeatureSuggestion]:
        """Search external sources and suggest similar features."""
        self.logger.info(f"Searching for similar features: {description}")
        
        try:
            async with self.search_client:
                # Search for implementations
                search_results = await self.search_client.comprehensive_search(description, language)
                
                suggestions = []
                
                # Convert search results to feature suggestions
                for source, results in search_results.items():
                    for result in results[:3]:  # Top 3 from each source
                        suggestion = await self._convert_search_result_to_suggestion(result, description)
                        if suggestion:
                            suggestions.append(suggestion)
                
                return suggestions[:10]  # Top 10 suggestions
                
        except Exception as e:
            self.logger.error(f"Error searching for similar features: {e}")
            return []
    
    async def _analyze_project_structure(self, project_path: str) -> Dict[str, Any]:
        """Analyze project structure and extract relevant information."""
        project_info = {
            'languages': set(),
            'frameworks': set(),
            'has_tests': False,
            'has_docs': False,
            'has_config': False,
            'has_database': False,
            'has_api': False,
            'has_web_interface': False,
            'has_cli': False,
            'file_count': 0,
            'python_features': set(),
            'missing_common_files': [],
            'project_type': 'unknown'
        }
        
        try:
            path = Path(project_path)
            
            # Analyze files
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    project_info['file_count'] += 1
                    
                    # Detect languages
                    suffix = file_path.suffix.lower()
                    if suffix in ['.py']:
                        project_info['languages'].add('python')
                        await self._analyze_python_file(file_path, project_info)
                    elif suffix in ['.js', '.jsx']:
                        project_info['languages'].add('javascript')
                    elif suffix in ['.ts', '.tsx']:
                        project_info['languages'].add('typescript')
                    elif suffix in ['.java']:
                        project_info['languages'].add('java')
                    elif suffix in ['.cpp', '.cc', '.cxx']:
                        project_info['languages'].add('cpp')
                    
                    # Detect frameworks and tools
                    filename = file_path.name.lower()
                    if filename in ['requirements.txt', 'setup.py', 'pyproject.toml']:
                        await self._analyze_python_dependencies(file_path, project_info)
                    elif filename == 'package.json':
                        await self._analyze_node_dependencies(file_path, project_info)
                    elif filename in ['dockerfile', 'docker-compose.yml']:
                        project_info['frameworks'].add('docker')
                    elif 'test' in filename:
                        project_info['has_tests'] = True
                    elif filename in ['readme.md', 'readme.txt', 'readme.rst']:
                        project_info['has_docs'] = True
                    elif filename in ['config.py', 'settings.py', '.env']:
                        project_info['has_config'] = True
            
            # Determine project type
            project_info['project_type'] = self._determine_project_type(project_info)
            
            # Find missing common files
            project_info['missing_common_files'] = self._find_missing_common_files(path, project_info)
            
        except Exception as e:
            self.logger.error(f"Error analyzing project structure: {e}")
        
        return project_info
    
    async def _analyze_python_file(self, file_path: Path, project_info: Dict[str, Any]):
        """Analyze a Python file for features and patterns."""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    module_name = getattr(node, 'module', None) or (node.names[0].name if node.names else '')
                    
                    # Detect frameworks
                    if 'django' in module_name:
                        project_info['frameworks'].add('django')
                        project_info['has_web_interface'] = True
                        project_info['has_database'] = True
                    elif 'flask' in module_name:
                        project_info['frameworks'].add('flask')
                        project_info['has_web_interface'] = True
                    elif 'fastapi' in module_name:
                        project_info['frameworks'].add('fastapi')
                        project_info['has_api'] = True
                    elif 'sqlalchemy' in module_name:
                        project_info['has_database'] = True
                    elif 'click' in module_name or 'argparse' in module_name:
                        project_info['has_cli'] = True
                    elif 'requests' in module_name or 'aiohttp' in module_name:
                        project_info['python_features'].add('http_client')
                    elif 'pytest' in module_name:
                        project_info['has_tests'] = True
                
                # Detect patterns
                if isinstance(node, ast.ClassDef):
                    if any(base.id == 'Exception' for base in node.bases if isinstance(base, ast.Name)):
                        project_info['python_features'].add('custom_exceptions')
                elif isinstance(node, ast.AsyncFunctionDef):
                    project_info['python_features'].add('async_functions')
                    
        except Exception as e:
            self.logger.debug(f"Error analyzing Python file {file_path}: {e}")
    
    async def _analyze_python_dependencies(self, file_path: Path, project_info: Dict[str, Any]):
        """Analyze Python dependency files."""
        try:
            content = file_path.read_text()
            
            # Common frameworks and libraries
            if 'django' in content.lower():
                project_info['frameworks'].add('django')
                project_info['has_web_interface'] = True
            if 'flask' in content.lower():
                project_info['frameworks'].add('flask')
                project_info['has_web_interface'] = True
            if 'fastapi' in content.lower():
                project_info['frameworks'].add('fastapi')
                project_info['has_api'] = True
            if 'streamlit' in content.lower():
                project_info['frameworks'].add('streamlit')
                project_info['has_web_interface'] = True
            if 'sqlite' in content.lower() or 'postgresql' in content.lower() or 'mysql' in content.lower():
                project_info['has_database'] = True
                
        except Exception as e:
            self.logger.debug(f"Error analyzing dependencies {file_path}: {e}")
    
    async def _analyze_node_dependencies(self, file_path: Path, project_info: Dict[str, Any]):
        """Analyze Node.js package.json."""
        try:
            content = json.loads(file_path.read_text())
            dependencies = {**content.get('dependencies', {}), **content.get('devDependencies', {})}
            
            if 'react' in dependencies:
                project_info['frameworks'].add('react')
                project_info['has_web_interface'] = True
            if 'vue' in dependencies:
                project_info['frameworks'].add('vue')
                project_info['has_web_interface'] = True
            if 'express' in dependencies:
                project_info['frameworks'].add('express')
                project_info['has_api'] = True
                
        except Exception as e:
            self.logger.debug(f"Error analyzing package.json {file_path}: {e}")
    
    def _determine_project_type(self, project_info: Dict[str, Any]) -> str:
        """Determine the project type based on analysis."""
        if project_info['has_web_interface']:
            return 'web_application'
        elif project_info['has_api']:
            return 'api_service'
        elif project_info['has_cli']:
            return 'cli_tool'
        elif 'python' in project_info['languages'] and project_info['file_count'] > 5:
            return 'python_library'
        else:
            return 'script_collection'
    
    def _find_missing_common_files(self, project_path: Path, project_info: Dict[str, Any]) -> List[str]:
        """Find common files that are missing from the project."""
        missing = []
        
        common_files = {
            '.gitignore': 'Git ignore file',
            'README.md': 'Project documentation',
            'LICENSE': 'License file',
            'requirements.txt': 'Python dependencies (for Python projects)',
            'setup.py': 'Python package setup (for Python libraries)',
            'Dockerfile': 'Container configuration',
            '.github/workflows/ci.yml': 'CI/CD pipeline',
            'tests/': 'Test directory',
            'docs/': 'Documentation directory'
        }
        
        for filename, description in common_files.items():
            if not (project_path / filename).exists():
                # Only suggest relevant files
                if filename == 'requirements.txt' and 'python' not in project_info['languages']:
                    continue
                if filename == 'setup.py' and project_info['project_type'] != 'python_library':
                    continue
                missing.append(filename)
        
        return missing
    
    async def _generate_rule_based_suggestions(self, project_info: Dict[str, Any]) -> List[FeatureSuggestion]:
        """Generate suggestions based on project analysis rules."""
        suggestions = []
        
        # Missing essential files
        if 'README.md' in project_info['missing_common_files']:
            suggestions.append(FeatureSuggestion(
                name="Add README Documentation",
                description="Create comprehensive README.md with project description, installation, and usage instructions",
                category="documentation",
                implementation_steps=[
                    "Create README.md file",
                    "Add project title and description",
                    "Add installation instructions",
                    "Add usage examples",
                    "Add contributing guidelines"
                ],
                files_to_create=["README.md"],
                files_to_modify=[],
                dependencies=[],
                examples=[],
                priority="high",
                confidence=0.9,
                estimated_effort="small"
            ))
        
        # Testing framework
        if not project_info['has_tests']:
            suggestions.append(FeatureSuggestion(
                name="Add Testing Framework",
                description="Implement comprehensive testing with pytest or similar framework",
                category="testing",
                implementation_steps=[
                    "Install testing framework (pytest for Python)",
                    "Create tests/ directory structure",
                    "Add unit tests for core functionality",
                    "Set up test configuration",
                    "Add CI/CD integration for automated testing"
                ],
                files_to_create=["tests/__init__.py", "tests/test_main.py", "pytest.ini"],
                files_to_modify=["requirements.txt"],
                dependencies=["pytest", "pytest-cov"],
                examples=[],
                priority="high",
                confidence=0.85,
                estimated_effort="medium"
            ))
        
        # Configuration management
        if not project_info['has_config'] and project_info['project_type'] in ['web_application', 'api_service']:
            suggestions.append(FeatureSuggestion(
                name="Add Configuration Management",
                description="Implement environment-based configuration system",
                category="configuration",
                implementation_steps=[
                    "Create configuration module",
                    "Add support for environment variables",
                    "Create development/production config files",
                    "Add configuration validation",
                    "Update code to use centralized configuration"
                ],
                files_to_create=["config.py", ".env.example", "configs/development.py"],
                files_to_modify=[],
                dependencies=["python-dotenv"],
                examples=[],
                priority="medium",
                confidence=0.8,
                estimated_effort="medium"
            ))
        
        # API documentation
        if project_info['has_api'] and 'fastapi' in project_info['frameworks']:
            suggestions.append(FeatureSuggestion(
                name="Enhanced API Documentation",
                description="Add comprehensive API documentation with examples and authentication",
                category="documentation",
                implementation_steps=[
                    "Add detailed docstrings to API endpoints",
                    "Configure Swagger/OpenAPI settings",
                    "Add request/response examples",
                    "Add authentication documentation",
                    "Create API usage guide"
                ],
                files_to_create=["docs/api_guide.md"],
                files_to_modify=["main.py"],
                dependencies=[],
                examples=[],
                priority="medium",
                confidence=0.85,
                estimated_effort="small"
            ))
        
        # Database migrations (for web apps without proper DB setup)
        if project_info['has_web_interface'] and not project_info['has_database']:
            suggestions.append(FeatureSuggestion(
                name="Add Database Integration",
                description="Implement database support with ORM and migrations",
                category="database",
                implementation_steps=[
                    "Choose and install database ORM (SQLAlchemy for Python)",
                    "Create database models",
                    "Set up database connection and configuration",
                    "Create migration system",
                    "Add database initialization scripts"
                ],
                files_to_create=["models.py", "database.py", "migrations/"],
                files_to_modify=["requirements.txt", "config.py"],
                dependencies=["sqlalchemy", "alembic"],
                examples=[],
                priority="high",
                confidence=0.8,
                estimated_effort="large"
            ))
        
        return suggestions
    
    async def _generate_template_based_suggestions(self, project_info: Dict[str, Any]) -> List[FeatureSuggestion]:
        """Generate suggestions based on predefined templates."""
        suggestions = []
        
        # Get relevant templates based on project type
        relevant_templates = self.feature_templates.get(project_info['project_type'], [])
        
        for template in relevant_templates:
            # Check if template is applicable
            if self._is_template_applicable(template, project_info):
                suggestion = FeatureSuggestion(
                    name=template['name'],
                    description=template['description'],
                    category=template['category'],
                    implementation_steps=template['implementation_steps'],
                    files_to_create=template['files_to_create'],
                    files_to_modify=template['files_to_modify'],
                    dependencies=template['dependencies'],
                    examples=[],
                    priority=template.get('priority', 'medium'),
                    confidence=template.get('confidence', 0.7),
                    estimated_effort=template.get('estimated_effort', 'medium')
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    async def _generate_search_based_suggestions(self, project_info: Dict[str, Any]) -> List[FeatureSuggestion]:
        """Generate suggestions based on external search results."""
        suggestions = []
        
        try:
            # Search for common features in similar projects
            search_queries = self._generate_search_queries(project_info)
            
            async with self.search_client:
                for query in search_queries[:3]:  # Limit to 3 queries to avoid rate limits
                    language = list(project_info['languages'])[0] if project_info['languages'] else None
                    results = await self.search_client.search_github_repositories(query, language, 5)
                    
                    for result in results[:2]:  # Top 2 results per query
                        suggestion = await self._analyze_repository_for_features(result, project_info)
                        if suggestion:
                            suggestions.append(suggestion)
        
        except Exception as e:
            self.logger.error(f"Error generating search-based suggestions: {e}")
        
        return suggestions
    
    def _generate_search_queries(self, project_info: Dict[str, Any]) -> List[str]:
        """Generate search queries based on project analysis."""
        queries = []
        
        project_type = project_info['project_type']
        languages = list(project_info['languages'])
        
        if project_type == 'web_application':
            queries.extend([
                "authentication system",
                "user management",
                "admin dashboard",
                "API rate limiting"
            ])
        elif project_type == 'api_service':
            queries.extend([
                "API middleware",
                "request validation",
                "response caching",
                "API monitoring"
            ])
        elif project_type == 'cli_tool':
            queries.extend([
                "CLI configuration",
                "command plugins",
                "progress bars",
                "logging system"
            ])
        
        return queries
    
    async def _analyze_repository_for_features(self, repo_result: SearchResult, project_info: Dict[str, Any]) -> Optional[FeatureSuggestion]:
        """Analyze a repository search result to extract feature suggestions."""
        # This is a simplified implementation
        # In practice, you might want to fetch and analyze the repository structure
        
        repo_name = repo_result.title.split('/')[-1]
        
        return FeatureSuggestion(
            name=f"Add {repo_name}-inspired Feature",
            description=f"Implement feature inspired by {repo_result.title}: {repo_result.snippet}",
            category="enhancement",
            implementation_steps=[
                f"Study implementation in {repo_result.title}",
                "Adapt feature to current project structure",
                "Implement core functionality",
                "Add tests and documentation"
            ],
            files_to_create=[f"{repo_name.lower()}_feature.py"],
            files_to_modify=[],
            dependencies=[],
            examples=[repo_result],
            priority="low",
            confidence=0.6,
            estimated_effort="medium"
        )
    
    async def _convert_search_result_to_suggestion(self, result: SearchResult, description: str) -> Optional[FeatureSuggestion]:
        """Convert a search result to a feature suggestion."""
        return FeatureSuggestion(
            name=f"Implement {result.title}",
            description=f"Based on search for '{description}': {result.snippet}",
            category="research",
            implementation_steps=[
                f"Review implementation at {result.url}",
                "Adapt code to project needs",
                "Test implementation",
                "Add documentation"
            ],
            files_to_create=[],
            files_to_modify=[],
            dependencies=[],
            examples=[result],
            priority="low",
            confidence=result.relevance_score,
            estimated_effort="medium"
        )
    
    def _is_template_applicable(self, template: Dict[str, Any], project_info: Dict[str, Any]) -> bool:
        """Check if a template is applicable to the current project."""
        # Check required conditions
        required_languages = template.get('required_languages', [])
        if required_languages and not any(lang in project_info['languages'] for lang in required_languages):
            return False
        
        required_frameworks = template.get('required_frameworks', [])
        if required_frameworks and not any(fw in project_info['frameworks'] for fw in required_frameworks):
            return False
        
        # Check exclusion conditions
        excluded_if = template.get('excluded_if', {})
        for condition, value in excluded_if.items():
            if project_info.get(condition) == value:
                return False
        
        return True
    
    def _load_feature_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load predefined feature templates."""
        return {
            'web_application': [
                {
                    'name': 'User Authentication System',
                    'description': 'Add comprehensive user authentication with login, registration, and session management',
                    'category': 'authentication',
                    'implementation_steps': [
                        'Install authentication library',
                        'Create user model and database tables',
                        'Implement login/logout endpoints',
                        'Add registration functionality',
                        'Create session management',
                        'Add password reset functionality'
                    ],
                    'files_to_create': ['auth.py', 'models/user.py', 'templates/login.html'],
                    'files_to_modify': ['main.py', 'requirements.txt'],
                    'dependencies': ['flask-login', 'werkzeug'],
                    'priority': 'high',
                    'confidence': 0.9,
                    'estimated_effort': 'large'
                },
                {
                    'name': 'Admin Dashboard',
                    'description': 'Create administrative interface for managing application data',
                    'category': 'administration',
                    'implementation_steps': [
                        'Create admin blueprint/module',
                        'Add admin authentication',
                        'Create data management interfaces',
                        'Add user management features',
                        'Implement logging and monitoring'
                    ],
                    'files_to_create': ['admin.py', 'templates/admin/'],
                    'files_to_modify': ['main.py'],
                    'dependencies': ['flask-admin'],
                    'priority': 'medium',
                    'confidence': 0.8,
                    'estimated_effort': 'large'
                }
            ],
            'api_service': [
                {
                    'name': 'API Rate Limiting',
                    'description': 'Implement rate limiting to prevent API abuse',
                    'category': 'security',
                    'implementation_steps': [
                        'Install rate limiting library',
                        'Configure rate limits per endpoint',
                        'Add rate limit headers',
                        'Implement custom rate limit responses',
                        'Add monitoring and alerts'
                    ],
                    'files_to_create': ['middleware/rate_limit.py'],
                    'files_to_modify': ['main.py'],
                    'dependencies': ['slowapi'],
                    'priority': 'high',
                    'confidence': 0.85,
                    'estimated_effort': 'medium'
                }
            ],
            'cli_tool': [
                {
                    'name': 'Plugin System',
                    'description': 'Add extensible plugin architecture for additional commands',
                    'category': 'extensibility',
                    'implementation_steps': [
                        'Design plugin interface',
                        'Create plugin discovery mechanism',
                        'Add plugin loading system',
                        'Create example plugins',
                        'Add plugin documentation'
                    ],
                    'files_to_create': ['plugins/', 'plugin_manager.py'],
                    'files_to_modify': ['main.py'],
                    'dependencies': [],
                    'priority': 'medium',
                    'confidence': 0.7,
                    'estimated_effort': 'large'
                }
            ]
        }
    
    def _priority_score(self, priority: str) -> int:
        """Convert priority string to numeric score for sorting."""
        return {'high': 3, 'medium': 2, 'low': 1}.get(priority, 2)
    
    def _get_fallback_suggestions(self, project_info: Dict[str, Any]) -> List[FeatureSuggestion]:
        """Get fallback suggestions when external search is not available."""
        fallback_suggestions = []
        
        # Common suggestions that apply to most projects
        common_features = [
            {
                'name': 'Configuration Management',
                'description': 'Centralized configuration system with environment support',
                'category': 'infrastructure',
                'steps': ['Create config module', 'Add .env support', 'Implement validation'],
                'files': ['config.py', '.env.example'],
                'deps': ['python-dotenv']
            },
            {
                'name': 'Logging System',
                'description': 'Structured logging with multiple output formats',
                'category': 'monitoring',
                'steps': ['Set up logger', 'Add formatters', 'Configure handlers'],
                'files': ['logging_config.py'],
                'deps': ['structlog']
            },
            {
                'name': 'Error Handling',
                'description': 'Comprehensive error handling and user-friendly error messages',
                'category': 'reliability',
                'steps': ['Create error classes', 'Add error handlers', 'Implement recovery'],
                'files': ['errors.py'],
                'deps': []
            }
        ]
        
        for feature in common_features:
            suggestion = FeatureSuggestion(
                name=feature['name'],
                description=feature['description'],
                category=feature['category'],
                implementation_steps=feature['steps'],
                files_to_create=feature['files'],
                files_to_modify=[],
                dependencies=feature['deps'],
                examples=[],
                priority="medium",
                confidence=0.7,
                estimated_effort="medium"
            )
            fallback_suggestions.append(suggestion)
        
        return fallback_suggestions
    
    def _get_additional_fallback_suggestions(self, project_info: Dict[str, Any]) -> List[FeatureSuggestion]:
        """Get additional fallback suggestions based on project type."""
        suggestions = []
        
        if project_info.get('has_web_framework'):
            suggestions.append(FeatureSuggestion(
                name="Health Check Endpoint",
                description="Add health monitoring endpoint for service status",
                category="monitoring",
                implementation_steps=["Create health endpoint", "Add system checks", "Include dependency status"],
                files_to_create=["health.py"],
                files_to_modify=["main.py"],
                dependencies=[],
                examples=[],
                priority="medium",
                confidence=0.8,
                estimated_effort="small"
            ))
        
        if project_info.get('has_database'):
            suggestions.append(FeatureSuggestion(
                name="Database Migration System",
                description="Automated database schema migration management",
                category="database",
                implementation_steps=["Set up migration framework", "Create initial migration", "Add migration commands"],
                files_to_create=["migrations/"],
                files_to_modify=[],
                dependencies=["alembic"],
                examples=[],
                priority="high",
                confidence=0.9,
                estimated_effort="medium"
            ))
        
        if not project_info.get('has_tests'):
            suggestions.append(FeatureSuggestion(
                name="Testing Framework Setup",
                description="Complete testing framework with unit and integration tests",
                category="testing",
                implementation_steps=["Install testing framework", "Create test structure", "Add sample tests"],
                files_to_create=["tests/", "conftest.py"],
                files_to_modify=[],
                dependencies=["pytest", "pytest-cov"],
                examples=[],
                priority="high",
                confidence=0.95,
                estimated_effort="medium"
            ))
        
        return suggestions
    
    def _get_basic_fallback_suggestions(self) -> List[FeatureSuggestion]:
        """Get basic fallback suggestions when everything else fails."""
        return [
            FeatureSuggestion(
                name="Documentation System",
                description="Automated documentation generation and maintenance",
                category="documentation",
                implementation_steps=["Set up doc generator", "Create doc templates", "Add API docs"],
                files_to_create=["docs/", "README.md"],
                files_to_modify=[],
                dependencies=["sphinx"],
                examples=[],
                priority="medium",
                confidence=0.8,
                estimated_effort="medium"
            ),
            FeatureSuggestion(
                name="Code Quality Tools",
                description="Automated code formatting, linting, and quality checks",
                category="development",
                implementation_steps=["Add linter config", "Set up formatter", "Create pre-commit hooks"],
                files_to_create=[".pre-commit-config.yaml", "pyproject.toml"],
                files_to_modify=[],
                dependencies=["black", "flake8", "pre-commit"],
                examples=[],
                priority="medium",
                confidence=0.9,
                estimated_effort="small"
            ),
            FeatureSuggestion(
                name="Performance Monitoring",
                description="Application performance monitoring and profiling",
                category="performance",
                implementation_steps=["Add profiling middleware", "Set up metrics collection", "Create dashboards"],
                files_to_create=["monitoring.py"],
                files_to_modify=[],
                dependencies=["psutil"],
                examples=[],
                priority="low",
                confidence=0.7,
                estimated_effort="medium"
            )
        ]