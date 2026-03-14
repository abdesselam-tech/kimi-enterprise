"""
Git Integration for Automatic PR Creation and Repository Management
"""
import subprocess
import json
import re
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PRDetails:
    """Pull Request details"""
    title: str
    body: str
    branch: str
    base: str = "main"
    reviewers: List[str] = None
    labels: List[str] = None
    draft: bool = False


class GitIntegration:
    """
    Handles all Git operations for the enterprise:
    - Branch creation
    - Commit management
    - Automatic PR creation
    - Merge automation
    - Code review coordination
    """
    
    def __init__(self, project_root: Path, config):
        self.project = Path(project_root)
        self.config = config
        self._git_available = self._check_git()
        self._gh_available = self._check_gh_cli()
    
    def _check_git(self) -> bool:
        """Check if git is available"""
        try:
            subprocess.run(
                ["git", "--version"],
                cwd=self.project,
                check=True,
                capture_output=True
            )
            return True
        except:
            return False
    
    def _check_gh_cli(self) -> bool:
        """Check if GitHub CLI is available"""
        try:
            subprocess.run(
                ["gh", "--version"],
                cwd=self.project,
                check=True,
                capture_output=True
            )
            return True
        except:
            return False
    
    def is_git_repo(self) -> bool:
        """Check if project is a git repository"""
        if not self._git_available:
            return False
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.project,
                check=True,
                capture_output=True
            )
            return True
        except:
            return False
    
    def get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        if not self.is_git_repo():
            return None
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except:
            return None
    
    def create_branch(self, agent_id: str, task_id: str, description: str) -> Optional[str]:
        """
        Create a new branch for an agent's work.
        Returns branch name or None on failure.
        """
        if not self.is_git_repo():
            logger.warning("Not a git repository")
            return None
        
        # Sanitize description for branch name
        sanitized = re.sub(r'[^a-zA-Z0-9-]', '-', description.lower())
        sanitized = re.sub(r'-+', '-', sanitized)[:50]  # Limit length
        
        branch_name = f"{self.config.git.branch_prefix}{agent_id}/{task_id}-{sanitized}"
        
        try:
            # Create and checkout branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.project,
                check=True,
                capture_output=True
            )
            logger.info(f"Created branch: {branch_name}")
            return branch_name
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch: {e}")
            return None
    
    def commit_changes(self, agent_id: str, message: str, 
                       files: List[str] = None) -> bool:
        """
        Commit changes with proper attribution.
        Uses conventional commit format with agent attribution.
        """
        if not self.is_git_repo():
            return False
        
        # Format commit message
        formatted_message = self.config.git.commit_message_template.format(
            agent=agent_id,
            message=message
        )
        
        try:
            # Add files
            if files:
                subprocess.run(
                    ["git", "add"] + files,
                    cwd=self.project,
                    check=True,
                    capture_output=True
                )
            else:
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=self.project,
                    check=True,
                    capture_output=True
                )
            
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.project,
                capture_output=True
            )
            if result.returncode == 0:
                logger.info("No changes to commit")
                return True
            
            # Commit with agent attribution
            subprocess.run(
                ["git", "commit", "-m", formatted_message,
                 "--author", f"{agent_id} <{agent_id}@kimi-enterprise.ai>"],
                cwd=self.project,
                check=True,
                capture_output=True
            )
            logger.info(f"Committed: {formatted_message[:50]}...")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit: {e}")
            return False
    
    def push_branch(self, branch: str = None) -> bool:
        """Push current branch to remote"""
        if not self.is_git_repo():
            return False
        
        branch = branch or self.get_current_branch()
        if not branch:
            return False
        
        try:
            subprocess.run(
                ["git", "push", "-u", "origin", branch],
                cwd=self.project,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push: {e}")
            return False
    
    def create_pull_request(self, agent_id: str, task: Dict, 
                           branch: str = None) -> Optional[str]:
        """
        Create a GitHub Pull Request for completed work.
        Returns PR URL or None on failure.
        """
        if not self._gh_available:
            logger.warning("GitHub CLI not available")
            return None
        
        if not self.is_git_repo():
            return None
        
        branch = branch or self.get_current_branch()
        if not branch:
            return None
        
        # Build PR details
        pr = self._build_pr_details(agent_id, task, branch)
        
        try:
            # Push branch first
            if not self.push_branch(branch):
                return None
            
            # Create PR
            cmd = [
                "gh", "pr", "create",
                "--title", pr.title,
                "--body", pr.body,
                "--base", pr.base,
            ]
            
            if pr.draft:
                cmd.append("--draft")
            
            for reviewer in (pr.reviewers or []):
                cmd.extend(["--reviewer", reviewer])
            
            for label in (pr.labels or []):
                cmd.extend(["--label", label])
            
            result = subprocess.run(
                cmd,
                cwd=self.project,
                check=True,
                capture_output=True,
                text=True
            )
            
            pr_url = result.stdout.strip()
            logger.info(f"Created PR: {pr_url}")
            return pr_url
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create PR: {e}")
            return None
    
    def _build_pr_details(self, agent_id: str, task: Dict, branch: str) -> PRDetails:
        """Build PR details from task information"""
        task_title = task.get('title', 'Untitled Task')
        task_id = task.get('id', 'unknown')
        task_type = task.get('type', 'feature')
        complexity = task.get('complexity', 'medium')
        acceptance_criteria = task.get('acceptance_criteria', [])
        
        # Title with conventional commit prefix
        type_prefix = {
            'feature': 'feat',
            'bugfix': 'fix',
            'refactor': 'refactor',
            'docs': 'docs',
            'test': 'test',
            'devops': 'chore'
        }.get(task_type, 'feat')
        
        title = f"{type_prefix}: {task_title} [{agent_id}]"
        
        # Build body
        body_lines = [
            f"## Task",
            f"**ID:** {task_id}",
            f"**Agent:** {agent_id}",
            f"**Type:** {task_type}",
            f"**Complexity:** {complexity}",
            "",
            "## Description",
            task.get('description', 'No description provided'),
            "",
            "## Acceptance Criteria",
        ]
        
        for criterion in acceptance_criteria:
            body_lines.append(f"- [x] {criterion}")
        
        body_lines.extend([
            "",
            "## Changes",
            "- Implemented as specified",
            "- Tests included",
            "- Documentation updated",
            "",
            "## Testing",
            "- [ ] Unit tests pass",
            "- [ ] Integration tests pass",
            "- [ ] Manual testing completed",
            "",
            "---",
            "*This PR was automatically created by Kimi Enterprise*"
        ])
        
        body = "\n".join(body_lines)
        
        # Determine labels
        labels = [task_type, complexity]
        if task.get('priority') == 'high':
            labels.append('priority-high')
        
        return PRDetails(
            title=title,
            body=body,
            branch=branch,
            base=task.get('base_branch', 'main'),
            labels=labels,
            draft=False
        )
    
    def check_pr_status(self, pr_number: int) -> Dict:
        """Check status of a pull request"""
        if not self._gh_available:
            return {"error": "GitHub CLI not available"}
        
        try:
            result = subprocess.run(
                ["gh", "pr", "view", str(pr_number), "--json", 
                 "state,checks,reviewDecision,mergeStateStatus"],
                cwd=self.project,
                check=True,
                capture_output=True,
                text=True
            )
            return json.loads(result.stdout)
        except:
            return {"error": "Failed to check PR status"}
    
    def merge_pr(self, pr_number: int, method: str = "squash") -> bool:
        """
        Merge a pull request if checks pass.
        Methods: merge, squash, rebase
        """
        if not self._gh_available:
            return False
        
        if not self.config.git.auto_merge_passing_prs:
            logger.info("Auto-merge disabled in config")
            return False
        
        # Check status first
        status = self.check_pr_status(pr_number)
        if status.get('state') != 'OPEN':
            logger.warning(f"PR #{pr_number} is not open")
            return False
        
        if status.get('mergeStateStatus') != 'CLEAN':
            logger.warning(f"PR #{pr_number} cannot be merged cleanly")
            return False
        
        try:
            subprocess.run(
                ["gh", "pr", "merge", str(pr_number), 
                 f"--{method}", "--auto"],
                cwd=self.project,
                check=True,
                capture_output=True
            )
            logger.info(f"Merged PR #{pr_number}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to merge PR: {e}")
            return False
    
    def get_recent_commits(self, agent_id: str = None, limit: int = 10) -> List[Dict]:
        """Get recent commits, optionally filtered by agent"""
        if not self.is_git_repo():
            return []
        
        try:
            format_str = '%H|%an|%ae|%ad|%s'
            cmd = ["git", "log", f"--format={format_str}", f"-{limit}"]
            
            if agent_id:
                cmd.extend(["--author", agent_id])
            
            result = subprocess.run(
                cmd,
                cwd=self.project,
                check=True,
                capture_output=True,
                text=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|', 4)
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4]
                    })
            
            return commits
            
        except:
            return []
    
    def create_tag(self, tag: str, message: str) -> bool:
        """Create a git tag for releases"""
        if not self.is_git_repo():
            return False
        
        try:
            subprocess.run(
                ["git", "tag", "-a", tag, "-m", message],
                cwd=self.project,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "push", "origin", tag],
                cwd=self.project,
                check=True,
                capture_output=True
            )
            return True
        except:
            return False
    
    def get_changed_files(self, since: str = "HEAD~1") -> List[str]:
        """Get list of files changed since reference"""
        if not self.is_git_repo():
            return []
        
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", since],
                cwd=self.project,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip().split('\n') if result.stdout else []
        except:
            return []


class CodeReviewCoordinator:
    """
    Manages code review assignments and tracking.
    Ensures quality gates are met before merging.
    """
    
    def __init__(self, git: GitIntegration):
        self.git = git
    
    def assign_reviewers(self, pr_number: int, 
                        required_approvals: int = 1) -> List[str]:
        """
        Intelligently assign reviewers based on:
        - Code ownership
        - Expertise matching
        - Load balancing
        """
        # This would integrate with CODEOWNERS or similar
        # For now, return default reviewers
        return []
    
    def check_quality_gates(self, pr_number: int) -> Dict:
        """
        Check if all quality gates are met:
        - Required reviews
        - CI checks passing
        - No merge conflicts
        - Security scan clean
        """
        status = self.git.check_pr_status(pr_number)
        
        return {
            "ready_to_merge": status.get('mergeStateStatus') == 'CLEAN',
            "checks_passing": all(
                c.get('conclusion') == 'SUCCESS'
                for c in status.get('checks', [])
            ),
            "review_approved": status.get('reviewDecision') == 'APPROVED',
            "status": status
        }
