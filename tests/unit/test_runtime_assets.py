from pathlib import Path


def test_docker_assets_exist_and_do_not_copy_env():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert 'ENTRYPOINT ["prompt-evolve"]' in dockerfile
    assert ".env" in dockerignore
    assert "env_file:" in compose
    assert "prompt-evolve" in compose


def test_init_scripts_create_expected_variables():
    ps1 = Path("scripts/init-env.ps1").read_text(encoding="utf-8")
    sh = Path("scripts/init-env.sh").read_text(encoding="utf-8")

    for content in (ps1, sh):
        assert "OPENROUTER_API_KEY" in content
        assert "GIGACHAT_CREDENTIALS" in content
        assert "GIGACHAT_BASE_URL" in content
        assert "prompt-evolve.yaml" in content


def test_local_setup_scripts_use_venv_and_module_launcher():
    setup_ps1 = Path("scripts/setup-local.ps1").read_text(encoding="utf-8")
    run_ps1 = Path("scripts/run-local.ps1").read_text(encoding="utf-8")
    setup_sh = Path("scripts/setup-local.sh").read_text(encoding="utf-8")
    run_sh = Path("scripts/run-local.sh").read_text(encoding="utf-8")

    assert "python -m venv" in setup_ps1
    assert "-m pip install -e" in setup_ps1
    assert "-m prompt_evolve.cli" in run_ps1
    assert "python3 -m venv" in setup_sh
    assert "-m pip install -e" in setup_sh
    assert "-m prompt_evolve.cli" in run_sh
