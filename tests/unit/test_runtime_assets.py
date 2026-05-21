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
