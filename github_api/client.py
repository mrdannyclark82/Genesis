"""GitHub API client for repository interactions."""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from github import Github, GithubException
import requests

from core.config import Config
from utils.logger import get_logger


class GitHubClient:
    """GitHub API client with comprehensive repository interaction capabilities."""
    
    def __init__(self, config: Config):
        """Initialize GitHub client."""
        self.config = config
        self.logger = get_logger(__name__)
        
        if not config.github_token:
            raise ValueError("GitHub token is required")
        
        self.github = Github(config.github_token)
        self.user = self.github.get_user()
        
        self.logger.info(f"GitHub client initialized for user: {self.user.login}")
    
    async def get_repository_info(self, repo_url: str) -> Dict[str, Any]:
        """Get comprehensive repository information."""
        try:
            # Parse repository URL to get owner and repo name
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            return {
                'owner': owner,
                'name': repo_name,
                'full_name': repo.full_name,
                'description': repo.description,
                'language': repo.language,
                'languages': dict(repo.get_languages()),
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'open_issues': repo.open_issues_count,
                'default_branch': repo.default_branch,
                'created_at': repo.created_at.isoformat(),
                'updated_at': repo.updated_at.isoformat(),
                'topics': repo.get_topics(),
                'has_issues': repo.has_issues,
                'has_projects': repo.has_projects,
                'has_wiki': repo.has_wiki,
                'archived': repo.archived,
                'private': repo.private,
            }
            
        except GithubException as e:
            self.logger.error(f"GitHub API error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error getting repository info: {e}")
            raise
    
    async def get_repository_structure(self, owner: str, repo_name: str, 
                                     branch: str = None) -> Dict[str, Any]:
        """Get repository file structure."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            branch = branch or repo.default_branch
            
            contents = repo.get_contents("", ref=branch)
            structure = await self._build_file_tree(repo, contents, branch)
            
            return {
                'branch': branch,
                'structure': structure,
                'total_files': self._count_files(structure),
            }
            
        except GithubException as e:
            self.logger.error(f"Error getting repository structure: {e}")
            raise
    
    async def get_file_content(self, owner: str, repo_name: str, 
                              file_path: str, branch: str = None) -> Dict[str, Any]:
        """Get content of a specific file."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            branch = branch or repo.default_branch
            
            file_content = repo.get_contents(file_path, ref=branch)
            
            return {
                'path': file_path,
                'name': file_content.name,
                'size': file_content.size,
                'encoding': file_content.encoding,
                'content': file_content.decoded_content.decode('utf-8'),
                'sha': file_content.sha,
                'download_url': file_content.download_url,
            }
            
        except GithubException as e:
            self.logger.error(f"Error getting file content: {e}")
            raise
    
    async def create_issue(self, owner: str, repo_name: str, title: str, 
                          body: str, labels: List[str] = None) -> Dict[str, Any]:
        """Create a new issue."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=labels or []
            )
            
            return {
                'number': issue.number,
                'title': issue.title,
                'body': issue.body,
                'state': issue.state,
                'url': issue.html_url,
                'created_at': issue.created_at.isoformat(),
            }
            
        except GithubException as e:
            self.logger.error(f"Error creating issue: {e}")
            raise
    
    async def create_pull_request(self, owner: str, repo_name: str, title: str,
                                 body: str, head: str, base: str) -> Dict[str, Any]:
        """Create a new pull request."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base
            )
            
            return {
                'number': pr.number,
                'title': pr.title,
                'body': pr.body,
                'state': pr.state,
                'url': pr.html_url,
                'head': pr.head.ref,
                'base': pr.base.ref,
                'created_at': pr.created_at.isoformat(),
            }
            
        except GithubException as e:
            self.logger.error(f"Error creating pull request: {e}")
            raise
    
    async def get_issues(self, owner: str, repo_name: str, 
                        state: str = 'open') -> List[Dict[str, Any]]:
        """Get repository issues."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            issues = repo.get_issues(state=state)
            
            return [
                {
                    'number': issue.number,
                    'title': issue.title,
                    'body': issue.body,
                    'state': issue.state,
                    'labels': [label.name for label in issue.labels],
                    'assignees': [assignee.login for assignee in issue.assignees],
                    'created_at': issue.created_at.isoformat(),
                    'updated_at': issue.updated_at.isoformat(),
                    'url': issue.html_url,
                }
                for issue in issues
            ]
            
        except GithubException as e:
            self.logger.error(f"Error getting issues: {e}")
            raise
    
    async def get_pull_requests(self, owner: str, repo_name: str,
                               state: str = 'open') -> List[Dict[str, Any]]:
        """Get repository pull requests."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            prs = repo.get_pulls(state=state)
            
            return [
                {
                    'number': pr.number,
                    'title': pr.title,
                    'body': pr.body,
                    'state': pr.state,
                    'head': pr.head.ref,
                    'base': pr.base.ref,
                    'mergeable': pr.mergeable,
                    'created_at': pr.created_at.isoformat(),
                    'updated_at': pr.updated_at.isoformat(),
                    'url': pr.html_url,
                }
                for pr in prs
            ]
            
        except GithubException as e:
            self.logger.error(f"Error getting pull requests: {e}")
            raise
    
    async def get_workflows(self, owner: str, repo_name: str) -> List[Dict[str, Any]]:
        """Get repository GitHub Actions workflows."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            workflows = repo.get_workflows()
            
            return [
                {
                    'id': workflow.id,
                    'name': workflow.name,
                    'path': workflow.path,
                    'state': workflow.state,
                    'created_at': workflow.created_at.isoformat(),
                    'updated_at': workflow.updated_at.isoformat(),
                    'url': workflow.html_url,
                }
                for workflow in workflows
            ]
            
        except GithubException as e:
            self.logger.error(f"Error getting workflows: {e}")
            raise
    
    async def update_file(self, owner: str, repo_name: str, file_path: str,
                         content: str, message: str, branch: str = None) -> Dict[str, Any]:
        """Update or create a file in the repository."""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            branch = branch or repo.default_branch
            
            try:
                # Try to get existing file
                file_info = repo.get_contents(file_path, ref=branch)
                # Update existing file
                result = repo.update_file(
                    path=file_path,
                    message=message,
                    content=content,
                    sha=file_info.sha,
                    branch=branch
                )
                action = 'updated'
            except GithubException:
                # Create new file
                result = repo.create_file(
                    path=file_path,
                    message=message,
                    content=content,
                    branch=branch
                )
                action = 'created'
            
            return {
                'action': action,
                'path': file_path,
                'sha': result['content'].sha,
                'url': result['content'].html_url,
            }
            
        except GithubException as e:
            self.logger.error(f"Error updating file: {e}")
            raise
    
    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """Parse repository URL to extract owner and repo name."""
        # Handle various URL formats
        if repo_url.startswith('https://github.com/'):
            parts = repo_url.replace('https://github.com/', '').split('/')
            return parts[0], parts[1].replace('.git', '')
        elif repo_url.startswith('git@github.com:'):
            parts = repo_url.replace('git@github.com:', '').split('/')
            return parts[0], parts[1].replace('.git', '')
        elif '/' in repo_url:
            # Assume format: owner/repo
            parts = repo_url.split('/')
            return parts[0], parts[1]
        else:
            raise ValueError(f"Invalid repository URL format: {repo_url}")
    
    async def _build_file_tree(self, repo, contents, branch: str, max_depth: int = 3,
                              current_depth: int = 0) -> List[Dict[str, Any]]:
        """Recursively build file tree structure."""
        if current_depth >= max_depth:
            return []
        
        tree = []
        for content in contents:
            item = {
                'name': content.name,
                'path': content.path,
                'type': content.type,
                'size': content.size,
            }
            
            if content.type == 'dir' and current_depth < max_depth - 1:
                try:
                    sub_contents = repo.get_contents(content.path, ref=branch)
                    item['children'] = await self._build_file_tree(
                        repo, sub_contents, branch, max_depth, current_depth + 1
                    )
                except GithubException:
                    # Skip directories we can't access
                    item['children'] = []
            
            tree.append(item)
        
        return tree
    
    def _count_files(self, structure: List[Dict[str, Any]]) -> int:
        """Count total files in structure."""
        count = 0
        for item in structure:
            if item['type'] == 'file':
                count += 1
            elif 'children' in item:
                count += self._count_files(item['children'])
        return count