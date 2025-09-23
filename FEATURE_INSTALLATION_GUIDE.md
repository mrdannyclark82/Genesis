# Genesis AI Agent - Feature Installation System

This guide covers the comprehensive feature installation and management system added to Genesis AI Agent.

## 🚀 Overview

The Genesis AI Agent now includes a powerful feature installation system that allows you to:

- Install pre-built features from templates
- Preview features before installation
- Manage dependencies automatically
- Track and rollback installations
- Create and manage custom personas
- Use a web dashboard for management

## 📦 Feature Installation Commands

### Install Features

```bash
# Install a single feature
python genesis.py install-feature user-auth

# Install multiple features at once
python genesis.py install-feature user-auth logging-system api-rate-limiting

# Auto-approve installation (skip confirmations)
python genesis.py install-feature user-auth --auto-approve

# Install to a specific directory
python genesis.py install-feature user-auth --target-dir ./my-project
```

### List and Preview Features

```bash
# List all available features
python genesis.py list-features

# List installed features
python genesis.py list-features --installed

# Preview a feature before installing
python genesis.py preview-feature user-auth
```

### Rollback Features

```bash
# Rollback a previously installed feature
python genesis.py rollback-feature user-auth
```

## 🎭 Enhanced Persona Management

### Basic Persona Commands

```bash
# List available personas
python genesis.py persona --list

# Set active persona
python genesis.py persona security_expert

# Check current persona status
python genesis.py persona --status
```

### Custom Persona Management

```bash
# Create a new persona interactively
python genesis.py create-persona --interactive

# Export a persona for sharing
python genesis.py export-persona security_expert -o my_security_expert.json

# Import a shared persona
python genesis.py import-persona custom_persona.json
```

## 🌐 Web Dashboard

### Start the Web Server

```bash
# Start on localhost:5000
python genesis.py serve

# Start on custom host/port
python genesis.py serve --host 0.0.0.0 --port 8080

# Start with debug mode
python genesis.py serve --debug
```

### Available API Endpoints

- `GET /api/health` - Health check
- `GET /api/features` - List available features
- `GET /api/features/<name>/preview` - Preview a feature
- `POST /api/features/<name>/install` - Install a feature
- `GET /api/features/installations` - List installed features
- `GET /api/personas` - List available personas
- `POST /api/personas/<name>/set` - Set active persona
- `POST /api/personas` - Create new persona
- `POST /api/analyze` - Analyze code
- `POST /api/suggest` - Get suggestions

## 🔧 Available Feature Templates

### 1. User Authentication System
- **Category**: Authentication
- **Files**: `auth.py`
- **Dependencies**: flask-login, werkzeug, bcrypt
- **Description**: Complete user authentication with login, registration, and session management

### 2. Advanced Logging System
- **Category**: Monitoring
- **Files**: `logger_config.py`
- **Dependencies**: structlog, python-json-logger
- **Description**: Structured logging with rotation and multiple handlers

### 3. API Rate Limiting
- **Category**: Security
- **Files**: `rate_limiter.py`
- **Dependencies**: flask-limiter, redis
- **Description**: Rate limiting to prevent API abuse and improve security

## 🎨 Interactive Mode Enhancements

The interactive mode now includes enhanced features:

```bash
python genesis.py interactive
```

New interactive commands:
- `install` - Interactive feature installation with search
- `list-features` - Browse available and installed features
- `serve` - Start web dashboard from interactive mode
- Enhanced `persona` command with guided selection

## 🔍 Enhanced CLI Features

### Fuzzy Search
When selecting features or personas, the system supports fuzzy matching:

```
Genesis> install
Enter feature name, search query, or command: auth
Found match: user-auth
```

### Rich Output
All commands now feature enhanced output with:
- Colored text and progress bars
- Tables for structured data
- Panels for feature previews
- Interactive prompts with validation

### Smart Suggestions
The system provides intelligent suggestions based on:
- Partial matches
- Category-based filtering
- Context-aware recommendations

## 🔐 Safety Features

### Backup and Rollback
- Automatic backup of existing files before modification
- Complete rollback capability for failed installations
- Installation tracking with timestamps and change logs

### Conflict Detection
- Warns about file overwrites before installation
- Provides detailed previews of changes
- Confirmation prompts for destructive operations

### Dependency Management
- Automatic `requirements.txt` updates
- Package installation with `pip`
- Dependency conflict detection

## 📝 Creating Custom Feature Templates

### Directory Structure
```
features/templates/my-feature/
├── feature.json
└── files/
    ├── main_file.py
    └── config/
        └── settings.json
```

### feature.json Format
```json
{
  "name": "My Custom Feature",
  "description": "Description of what this feature does",
  "category": "utility",
  "version": "1.0.0",
  "requirements": [
    "package1>=1.0.0",
    "package2>=2.0.0"
  ],
  "dependencies": [
    "External service configuration",
    "Database setup required"
  ],
  "post_install_steps": [
    "Configure environment variables",
    "Run initial setup command",
    "Test the installation"
  ]
}
```

## 🧪 Examples and Use Cases

### Scenario 1: Setting up Authentication
```bash
# Preview the authentication feature
python genesis.py preview-feature user-auth

# Install with confirmation
python genesis.py install-feature user-auth

# Verify installation
python genesis.py list-features --installed
```

### Scenario 2: Batch Feature Installation
```bash
# Install multiple security-focused features
python genesis.py install-feature user-auth api-rate-limiting --auto-approve

# Check what was installed
python genesis.py list-features --installed
```

### Scenario 3: Custom Persona Workflow
```bash
# Create a custom persona for your team
python genesis.py create-persona --interactive

# Export for sharing with team
python genesis.py export-persona my_custom_persona

# Team members can import it
python genesis.py import-persona my_custom_persona.json
```

### Scenario 4: Web Dashboard Management
```bash
# Start the web server
python genesis.py serve

# Access dashboard at http://localhost:5000
# Use the web interface to:
# - Browse and install features
# - Manage personas
# - Analyze code
# - View installation history
```

## 🔧 Troubleshooting

### Common Issues

1. **Installation Fails**: Check that you have write permissions in the target directory
2. **Dependency Conflicts**: Review the preview before installation to see what packages will be added
3. **Web Server Won't Start**: Ensure port 5000 is available or use `--port` to specify a different port
4. **Rollback Issues**: Check that backup files exist in `features/backups/`

### Getting Help

```bash
# General help
python genesis.py --help

# Command-specific help
python genesis.py install-feature --help
python genesis.py create-persona --help

# Interactive help
python genesis.py interactive
Genesis> help
```

## 🎉 Summary

The enhanced Genesis AI Agent now provides:

✅ **Feature Installation System** - Easy installation of pre-built components  
✅ **Enhanced CLI UX** - Rich output, fuzzy search, interactive prompts  
✅ **Persona System Improvements** - Custom persona creation and sharing  
✅ **Web Dashboard** - Full-featured web interface for management  
✅ **Safety Features** - Backup, rollback, and conflict detection  
✅ **Comprehensive Documentation** - Detailed guides and examples  

Start exploring these new capabilities to supercharge your development workflow!