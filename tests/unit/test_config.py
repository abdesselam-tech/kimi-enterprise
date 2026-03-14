"""
Unit tests for configuration management
"""
import pytest
import tempfile
import json
from pathlib import Path

# Add lib to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from kimi_enterprise.config import (
    EnterpriseConfig,
    ScalingConfig,
    CostConfig,
    GitConfig,
    AGENT_TIERS
)


class TestScalingConfig:
    """Test scaling configuration"""
    
    def test_default_values(self):
        config = ScalingConfig()
        assert config.enabled is True
        assert config.scale_up_threshold == 10
        assert config.scale_down_threshold == 2
        assert config.max_agents == 30
        assert config.min_agents == 2
        assert config.cooldown_minutes == 5
    
    def test_custom_values(self):
        config = ScalingConfig(
            enabled=False,
            max_agents=50,
            min_agents=5
        )
        assert config.enabled is False
        assert config.max_agents == 50
        assert config.min_agents == 5


class TestCostConfig:
    """Test cost configuration"""
    
    def test_default_budget(self):
        config = CostConfig()
        assert config.daily_budget_usd == 50.0
        assert config.emergency_halt_threshold == 0.95
        assert config.austerity_threshold == 0.75
    
    def test_thresholds_are_valid(self):
        config = CostConfig()
        assert 0 < config.warning_threshold < config.austerity_threshold < config.emergency_halt_threshold < 1


class TestGitConfig:
    """Test git configuration"""
    
    def test_defaults(self):
        config = GitConfig()
        assert config.enabled is True
        assert config.auto_create_prs is True
        assert config.branch_prefix == "ke/"


class TestEnterpriseConfig:
    """Test main configuration"""
    
    def test_default_initialization(self):
        config = EnterpriseConfig()
        assert config.name == "KimiEnterprise"
        assert config.version == "2.0.0"
        assert config.template == "full"
        assert config.scaling is not None
        assert config.costs is not None
        assert config.git is not None
    
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            # Create and save config
            config = EnterpriseConfig(
                name="TestProject",
                template="startup",
                costs=CostConfig(daily_budget_usd=100.0)
            )
            config.save(config_path)
            
            # Verify file exists
            assert config_path.exists()
            
            # Load and verify
            loaded = EnterpriseConfig.load(config_path)
            assert loaded.name == "TestProject"
            assert loaded.template == "startup"
            assert loaded.costs.daily_budget_usd == 100.0
    
    def test_load_nonexistent_returns_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.json"
            config = EnterpriseConfig.load(config_path)
            assert isinstance(config, EnterpriseConfig)


class TestAgentTiers:
    """Test agent tier definitions"""
    
    def test_tiers_exist(self):
        assert "executive" in AGENT_TIERS
        assert "senior" in AGENT_TIERS
        assert "junior" in AGENT_TIERS
    
    def test_tier_costs_are_positive(self):
        for tier_name, tier in AGENT_TIERS.items():
            assert tier.hourly_rate > 0, f"{tier_name} must have positive hourly rate"
    
    def test_executive_is_most_expensive(self):
        executive_rate = AGENT_TIERS["executive"].hourly_rate
        for tier_name, tier in AGENT_TIERS.items():
            assert tier.hourly_rate <= executive_rate, f"{tier_name} should not cost more than executive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
