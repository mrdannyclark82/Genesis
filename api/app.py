"""Genesis AI Agent Web API - Flask-based REST API for web dashboard."""

import os
import asyncio
from typing import Dict, List, Any, Optional

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

from core.config import Config
from core.agent import GenesisAgent
from features.installer import FeatureInstaller
from personas.persona_manager import PersonaManager
from utils.logger import get_logger


# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web dashboard

# Configuration
config = Config()
logger = get_logger(__name__)

# Initialize components
agent = None
installer = None
persona_manager = None


def init_components():
    """Initialize Genesis components."""
    global agent, installer, persona_manager
    try:
        agent = GenesisAgent()
        installer = FeatureInstaller(config)
        persona_manager = PersonaManager(config)
        logger.info("API components initialized")
    except Exception as e:
        logger.error(f"Error initializing components: {e}")


# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'components': {
            'agent': agent is not None,
            'installer': installer is not None,
            'persona_manager': persona_manager is not None
        }
    })


@app.route('/api/features', methods=['GET'])
def list_features():
    """Get available features for installation."""
    try:
        if not installer:
            return jsonify({'error': 'Installer not initialized'}), 500
        
        features = installer.get_available_features()
        feature_info = []
        
        for feature_name in features:
            info = installer.get_feature_info(feature_name)
            if info:
                feature_info.append({
                    'name': info.name,
                    'description': info.description,
                    'category': info.category,
                    'version': info.version,
                    'requirements': info.requirements,
                    'dependencies': info.dependencies
                })
        
        return jsonify({
            'features': feature_info,
            'count': len(feature_info)
        })
        
    except Exception as e:
        logger.error(f"Error listing features: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/features/<feature_name>/preview', methods=['GET'])
def preview_feature_api(feature_name: str):
    """Preview a feature before installation."""
    try:
        if not installer:
            return jsonify({'error': 'Installer not initialized'}), 500
        
        feature = installer.get_feature_info(feature_name)
        if not feature:
            return jsonify({'error': f'Feature {feature_name} not found'}), 404
        
        return jsonify({
            'name': feature.name,
            'description': feature.description,
            'category': feature.category,
            'version': feature.version,
            'files': list(feature.files.keys()),
            'requirements': feature.requirements,
            'dependencies': feature.dependencies,
            'post_install_steps': feature.post_install_steps
        })
        
    except Exception as e:
        logger.error(f"Error previewing feature: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/features/<feature_name>/install', methods=['POST'])
def install_feature_api(feature_name: str):
    """Install a feature."""
    try:
        if not installer:
            return jsonify({'error': 'Installer not initialized'}), 500
        
        data = request.get_json() or {}
        auto_approve = data.get('auto_approve', False)
        target_dir = data.get('target_dir', '.')
        
        # Run installation asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(
            installer.install_feature(feature_name, auto_approve, target_dir)
        )
        loop.close()
        
        return jsonify({
            'success': success,
            'feature': feature_name,
            'message': f'Feature {feature_name} {"installed successfully" if success else "installation failed"}'
        })
        
    except Exception as e:
        logger.error(f"Error installing feature: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/features/installations', methods=['GET'])
def list_installations_api():
    """List installed features."""
    try:
        if not installer:
            return jsonify({'error': 'Installer not initialized'}), 500
        
        installations = installer.list_installations()
        
        return jsonify({
            'installations': [
                {
                    'feature_name': record.feature_name,
                    'timestamp': record.timestamp,
                    'success': record.success,
                    'files_created': record.files_created,
                    'files_modified': record.files_modified,
                    'dependencies_added': record.dependencies_added
                }
                for record in installations
            ],
            'count': len(installations)
        })
        
    except Exception as e:
        logger.error(f"Error listing installations: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/personas', methods=['GET'])
def list_personas_api():
    """Get available personas."""
    try:
        if not persona_manager:
            return jsonify({'error': 'Persona manager not initialized'}), 500
        
        personas = persona_manager.get_available_personas()
        persona_info = []
        
        for persona_name in personas:
            info = persona_manager.get_persona_info(persona_name)
            if info:
                persona_info.append({
                    'name': info['name'],
                    'description': info['description'],
                    'expertise_areas': info['expertise_areas'],
                    'communication_style': info['communication_style'],
                    'focus_areas': info['focus_areas'],
                    'is_current': persona_manager.current_persona and persona_manager.current_persona.name == info['name']
                })
        
        return jsonify({
            'personas': persona_info,
            'count': len(persona_info)
        })
        
    except Exception as e:
        logger.error(f"Error listing personas: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/personas/<persona_name>/set', methods=['POST'])
def set_persona_api(persona_name: str):
    """Set active persona."""
    try:
        if not persona_manager:
            return jsonify({'error': 'Persona manager not initialized'}), 500
        
        success = persona_manager.set_persona(persona_name)
        
        if success:
            current = persona_manager.get_current_persona()
            return jsonify({
                'success': True,
                'persona': {
                    'name': current.name,
                    'description': current.description
                }
            })
        else:
            return jsonify({'error': f'Persona {persona_name} not found'}), 404
        
    except Exception as e:
        logger.error(f"Error setting persona: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/personas', methods=['POST'])
def create_persona_api():
    """Create a new persona."""
    try:
        if not persona_manager:
            return jsonify({'error': 'Persona manager not initialized'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No persona data provided'}), 400
        
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Persona name is required'}), 400
        
        success = persona_manager.create_custom_persona(name, data)
        
        return jsonify({
            'success': success,
            'message': f'Persona {name} {"created successfully" if success else "creation failed"}'
        })
        
    except Exception as e:
        logger.error(f"Error creating persona: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_code_api():
    """Analyze code."""
    try:
        if not agent:
            return jsonify({'error': 'Agent not initialized'}), 500
        
        data = request.get_json() or {}
        path = data.get('path', '.')
        
        # Run analysis asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(agent.analyze_code(path))
        loop.close()
        
        return jsonify({
            'results': results,
            'path': path,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error analyzing code: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/suggest', methods=['POST'])
def suggest_improvements_api():
    """Suggest improvements."""
    try:
        if not agent:
            return jsonify({'error': 'Agent not initialized'}), 500
        
        data = request.get_json() or {}
        repo_url = data.get('repo_url')
        
        # Run suggestion asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        suggestions = loop.run_until_complete(agent.suggest_improvements(repo_url))
        loop.close()
        
        return jsonify({
            'suggestions': suggestions,
            'count': len(suggestions)
        })
        
    except Exception as e:
        logger.error(f"Error suggesting improvements: {e}")
        return jsonify({'error': str(e)}), 500


# Web Dashboard Routes (Basic HTML)

@app.route('/')
def dashboard():
    """Basic web dashboard."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Genesis AI Agent Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; margin-bottom: 30px; }
            .section { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
            .section h2 { color: #666; margin-top: 0; }
            .btn { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #005c8a; }
            .api-link { color: #007cba; text-decoration: none; }
            .api-link:hover { text-decoration: underline; }
            .status { padding: 10px; border-radius: 4px; margin: 10px 0; }
            .status.healthy { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Genesis AI Agent Dashboard</h1>
            
            <div class="status healthy">
                <strong>Status:</strong> API Server Running
            </div>
            
            <div class="section">
                <h2>📦 Feature Management</h2>
                <p>Manage and install features for your project.</p>
                <button class="btn" onclick="loadFeatures()">Load Available Features</button>
                <button class="btn" onclick="loadInstallations()">View Installations</button>
                <div id="features-content"></div>
            </div>
            
            <div class="section">
                <h2>👤 Persona Management</h2>
                <p>Manage AI agent personas and communication styles.</p>
                <button class="btn" onclick="loadPersonas()">Load Personas</button>
                <div id="personas-content"></div>
            </div>
            
            <div class="section">
                <h2>🔍 Code Analysis</h2>
                <p>Analyze your code and get suggestions.</p>
                <button class="btn" onclick="analyzeCode()">Analyze Current Directory</button>
                <button class="btn" onclick="getSuggestions()">Get Suggestions</button>
                <div id="analysis-content"></div>
            </div>
            
            <div class="section">
                <h2>🔗 API Endpoints</h2>
                <ul>
                    <li><a href="/api/health" class="api-link">GET /api/health</a> - Health check</li>
                    <li><a href="/api/features" class="api-link">GET /api/features</a> - List features</li>
                    <li><a href="/api/personas" class="api-link">GET /api/personas</a> - List personas</li>
                    <li><a href="/api/features/installations" class="api-link">GET /api/features/installations</a> - List installations</li>
                </ul>
            </div>
        </div>
        
        <script>
            async function apiCall(url, options = {}) {
                try {
                    const response = await fetch(url, options);
                    return await response.json();
                } catch (error) {
                    console.error('API call failed:', error);
                    return { error: error.message };
                }
            }
            
            async function loadFeatures() {
                const content = document.getElementById('features-content');
                content.innerHTML = '<p>Loading...</p>';
                
                const data = await apiCall('/api/features');
                if (data.error) {
                    content.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                    return;
                }
                
                let html = `<h3>Available Features (${data.count})</h3><ul>`;
                data.features.forEach(feature => {
                    html += `<li><strong>${feature.name}</strong> - ${feature.description}</li>`;
                });
                html += '</ul>';
                content.innerHTML = html;
            }
            
            async function loadPersonas() {
                const content = document.getElementById('personas-content');
                content.innerHTML = '<p>Loading...</p>';
                
                const data = await apiCall('/api/personas');
                if (data.error) {
                    content.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                    return;
                }
                
                let html = `<h3>Available Personas (${data.count})</h3><ul>`;
                data.personas.forEach(persona => {
                    const current = persona.is_current ? ' (Current)' : '';
                    html += `<li><strong>${persona.name}</strong>${current} - ${persona.description}</li>`;
                });
                html += '</ul>';
                content.innerHTML = html;
            }
            
            async function loadInstallations() {
                const content = document.getElementById('features-content');
                content.innerHTML = '<p>Loading...</p>';
                
                const data = await apiCall('/api/features/installations');
                if (data.error) {
                    content.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                    return;
                }
                
                let html = `<h3>Installed Features (${data.count})</h3><ul>`;
                data.installations.forEach(install => {
                    const status = install.success ? '✅' : '❌';
                    html += `<li>${status} <strong>${install.feature_name}</strong> - ${install.timestamp}</li>`;
                });
                html += '</ul>';
                content.innerHTML = html;
            }
            
            async function analyzeCode() {
                const content = document.getElementById('analysis-content');
                content.innerHTML = '<p>Analyzing...</p>';
                
                const data = await apiCall('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: '.' })
                });
                
                if (data.error) {
                    content.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                    return;
                }
                
                let html = `<h3>Analysis Results (${data.count})</h3><ul>`;
                data.results.forEach(result => {
                    html += `<li>${result}</li>`;
                });
                html += '</ul>';
                content.innerHTML = html;
            }
            
            async function getSuggestions() {
                const content = document.getElementById('analysis-content');
                content.innerHTML = '<p>Getting suggestions...</p>';
                
                const data = await apiCall('/api/suggest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                
                if (data.error) {
                    content.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                    return;
                }
                
                let html = `<h3>Suggestions (${data.count})</h3><ul>`;
                data.suggestions.forEach(suggestion => {
                    html += `<li>${suggestion}</li>`;
                });
                html += '</ul>';
                content.innerHTML = html;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


# CLI command to run the web server
def run_web_server(host='127.0.0.1', port=5000, debug=False):
    """Run the Genesis web API server."""
    init_components()
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    init_components()
    app.run(debug=True, port=5000)