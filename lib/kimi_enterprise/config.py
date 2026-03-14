"""
Configuration management for Kimi Enterprise
"""
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict


@dataclass
class ScalingConfig:
    """Dynamic scaling configuration"""
    enabled: bool = True
    scale_up_threshold: int = 10  # Queue depth to trigger scale-up
    scale_down_threshold: int = 2  # Queue depth to trigger scale-down
    max_agents: int = 30
    min_agents: int = 2
    cooldown_minutes: int = 5
    scale_up_agents: int = 2  # How many to add per scale event


@dataclass
class CostConfig:
    """Cost optimization configuration"""
    daily_budget_usd: float = 50.0
    hourly_budget_usd: float = 5.0
    emergency_halt_threshold: float = 0.95  # 95% of budget
    austerity_threshold: float = 0.75  # 75% of budget
    warning_threshold: float = 0.50  # 50% of budget
    token_cost_per_1k_input: float = 0.01  # Kimi API pricing
    token_cost_per_1k_output: float = 0.03
    enable_predictive_scaling: bool = True  # Scale based on forecast


@dataclass
class GitConfig:
    """Git integration configuration"""
    enabled: bool = True
    auto_create_prs: bool = True
    pr_template: str = "enterprise"
    require_reviews: int = 1
    auto_merge_passing_prs: bool = False
    branch_prefix: str = "ke/"
    commit_message_template: str = "[KE-{agent}] {message}"


@dataclass
class AgentTier:
    """Cost tier for different agent levels"""
    name: str
    hourly_rate: float  # Approximate API cost per hour
    context_window: int = 256000
    priority: str = "normal"


AGENT_TIERS = {
    "executive": AgentTier("executive", hourly_rate=2.0, priority="high"),
    "director": AgentTier("director", hourly_rate=1.5, priority="high"),
    "manager": AgentTier("manager", hourly_rate=1.0, priority="normal"),
    "senior": AgentTier("senior", hourly_rate=0.8, priority="normal"),
    "mid": AgentTier("mid", hourly_rate=0.5, priority="normal"),
    "junior": AgentTier("junior", hourly_rate=0.3, priority="low"),
}


@dataclass
class EnterpriseConfig:
    """Main configuration class"""
    name: str = "KimiEnterprise"
    version: str = "2.0.0"
    template: str = "full"
    scaling: ScalingConfig = None
    costs: CostConfig = None
    git: GitConfig = None
    audit_level: str = "full"
    chain_of_command: str = "strict"
    enable_forecasting: bool = True
    enable_anomaly_detection: bool = True
    
    def __post_init__(self):
        if self.scaling is None:
            self.scaling = ScalingConfig()
        if self.costs is None:
            self.costs = CostConfig()
        if self.git is None:
            self.git = GitConfig()
    
    @classmethod
    def load(cls, path: Path) -> "EnterpriseConfig":
        """Load configuration from JSON file"""
        if not path.exists():
            return cls()
        
        with open(path) as f:
            data = json.load(f)
        
        # Parse nested configs
        scaling = ScalingConfig(**data.pop("scaling", {}))
        costs = CostConfig(**data.pop("costs", {}))
        git = GitConfig(**data.pop("git", {}))
        
        return cls(
            scaling=scaling,
            costs=costs,
            git=git,
            **data
        )
    
    def save(self, path: Path):
        """Save configuration to JSON file"""
        data = asdict(self)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


class ProjectConfig:
    """Per-project configuration manager"""
    
    def __init__(self, project_root: Path):
        self.root = project_root
        self.manifest_path = project_root / "kimi.json"
        self.config_path = project_root / ".kimi-enterprise" / "config.json"
        self._config: Optional[EnterpriseConfig] = None
    
    @property
    def exists(self) -> bool:
        return self.manifest_path.exists()
    
    @property
    def config(self) -> EnterpriseConfig:
        if self._config is None:
            self._config = EnterpriseConfig.load(self.config_path)
        return self._config
    
    def load_manifest(self) -> Dict:
        """Load project manifest"""
        if not self.exists:
            return {}
        with open(self.manifest_path) as f:
            return json.load(f)
    
    def save_manifest(self, manifest: Dict):
        """Save project manifest"""
        with open(self.manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
