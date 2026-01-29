"""Tests for configuration parsing."""
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from render_dashboard.config import (
    load_config,
    find_service_by_alias,
    ConfigError,
    AppConfig,
)
from render_dashboard.models import ServiceConfig


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid config file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "render": {
                "api_key": "test-key",
                "refresh_interval": 60,
            },
            "services": [
                {
                    "id": "srv-123",
                    "name": "Test Service",
                    "aliases": ["test", "ts"],
                    "priority": 1,
                }
            ],
        }
        config_file.write_text(yaml.dump(config_data))

        config = load_config(config_file)

        assert config.render.api_key == "test-key"
        assert config.render.refresh_interval == 60
        assert len(config.services) == 1
        assert config.services[0].id == "srv-123"
        assert config.services[0].name == "Test Service"
        assert config.services[0].aliases == ["test", "ts"]

    def test_env_var_substitution(self, tmp_path, monkeypatch):
        """Test environment variable substitution."""
        monkeypatch.setenv("TEST_API_KEY", "secret-key-123")

        config_file = tmp_path / "config.yaml"
        config_data = {
            "render": {
                "api_key": "${TEST_API_KEY}",
            },
            "services": [
                {"id": "srv-123", "name": "Test", "aliases": ["test"]},
            ],
        }
        config_file.write_text(yaml.dump(config_data))

        config = load_config(config_file)
        assert config.render.api_key == "secret-key-123"

    def test_missing_env_var_raises_error(self, tmp_path, monkeypatch):
        """Test that missing env var raises ConfigError."""
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)

        config_file = tmp_path / "config.yaml"
        config_data = {
            "render": {
                "api_key": "${NONEXISTENT_VAR}",
            },
            "services": [],
        }
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigError, match="Environment variable"):
            load_config(config_file, allow_empty_services=True)

    def test_missing_config_file_raises_error(self, tmp_path):
        """Test that missing config file raises ConfigError."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(ConfigError, match="not found"):
            load_config(config_file)

    def test_empty_services_raises_error(self, tmp_path):
        """Test that empty services list raises error by default."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "render": {"api_key": "test-key"},
            "services": [],
        }
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigError, match="No services configured"):
            load_config(config_file)

    def test_empty_services_allowed_with_flag(self, tmp_path):
        """Test that empty services allowed with flag."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "render": {"api_key": "test-key"},
            "services": [],
        }
        config_file.write_text(yaml.dump(config_data))

        config = load_config(config_file, allow_empty_services=True)
        assert len(config.services) == 0


class TestFindServiceByAlias:
    """Tests for find_service_by_alias function."""

    @pytest.fixture
    def config(self):
        """Create a test config with multiple services."""
        from render_dashboard.config import RenderConfig

        return AppConfig(
            render=RenderConfig(api_key="test"),
            services=[
                ServiceConfig(id="srv-1", name="Chat Server", aliases=["chat", "ch"]),
                ServiceConfig(id="srv-2", name="Auth Service", aliases=["auth"]),
                ServiceConfig(id="srv-3", name="API Gateway", aliases=["api", "gateway"]),
            ],
        )

    def test_exact_alias_match(self, config):
        """Test exact alias matching."""
        service = find_service_by_alias(config, "chat")
        assert service.id == "srv-1"

    def test_case_insensitive_match(self, config):
        """Test case insensitive matching."""
        service = find_service_by_alias(config, "CHAT")
        assert service.id == "srv-1"

    def test_partial_alias_match(self, config):
        """Test partial alias matching."""
        service = find_service_by_alias(config, "cha")
        assert service.id == "srv-1"

    def test_partial_name_match(self, config):
        """Test partial name matching."""
        service = find_service_by_alias(config, "Gateway")
        assert service.id == "srv-3"

    def test_no_match_returns_none(self, config):
        """Test that no match returns None."""
        service = find_service_by_alias(config, "nonexistent")
        assert service is None

    def test_multiple_matches_raises_error(self, config):
        """Test that multiple matches raises ConfigError."""
        # "a" matches both "auth" and "api"
        with pytest.raises(ConfigError, match="Multiple services match"):
            find_service_by_alias(config, "a")
