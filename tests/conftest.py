"""Shared fixtures for the test suite.

Tests that need DB/Redis should use the `db` and `redis` fixtures.
Tests that only need the pipeline logic can run without any infra.
"""
from __future__ import annotations

import os

import pytest

# Point at test databases so we never hit prod.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://shitposter:shitposter@localhost:5432/shitposter_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")
