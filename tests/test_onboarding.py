import os
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

import circuitron.onboarding as ob


def test_run_onboarding_writes_env(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    env_path = Path(tmp_path, ".circuitron", ".env")
    monkeypatch.setattr(ob, "ENV_FILE", env_path)
    env_path.parent.mkdir(parents=True, exist_ok=True)
    inputs = iter(["k", "surl", "skey", "uri", "user", "pass"])
    monkeypatch.setattr(ob.click, "prompt", lambda *_a, **_k: next(inputs))
    ob.run_onboarding()
    env = Path(tmp_path, ".circuitron", ".env")
    data = env.read_text()
    assert "OPENAI_API_KEY='k'" in data
    assert "SUPABASE_URL='surl'" in data
    assert "NEO4J_USER='user'" in data
