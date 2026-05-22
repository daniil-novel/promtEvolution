import json

from prompt_evolve.clarify import build_clarification_questions, build_task_spec
from prompt_evolve.inspo import mutate_instruction, reflect_failures, run_inspo_evolution
from prompt_evolve.mcp_tools import infer_tool_policy, load_mcp_config
from prompt_evolve.models import EvaluationResult, PromptCandidate, PromptRunResult, RewardWeights, TaskSpec
from prompt_evolve.providers import MockProvider
from prompt_evolve.rewards import cost_efficiency_score, reward_score, tool_usage_quality_score
from prompt_evolve.trajectories import ReplayBuffer, TrajectoryRecord
from tests.unit.test_prompts_evaluator_scope_metrics import case, result


def test_clarification_questions_include_json_and_uncertainty():
    questions = build_clarification_questions("Отвечай JSON. При сомнении делай reroute.", max_questions=3)
    assert len(questions) == 3
    assert any("JSON" in item for item in questions)


def test_build_task_spec_falls_back_with_mock_provider():
    spec = build_task_spec("Сделай ревью ответа", "Prompt", MockProvider())
    assert spec.objective
    assert spec.success_criteria
    assert spec.clarification_questions


def test_tool_policy_and_mcp_config(tmp_path):
    config = tmp_path / "mcp.json"
    config.write_text(json.dumps({"servers": {"github": {"command": "x"}}}), encoding="utf-8")
    loaded = load_mcp_config(config)
    policy = infer_tool_policy(
        TaskSpec(
            objective="Task",
            input_contract="Input",
            output_contract="Output",
            success_criteria=["Works"],
            failure_modes=["Fails"],
            tool_requirements=["Use GitHub only for repository context."],
        ),
        mcp_config=loaded,
    )
    assert policy.allowed_tools == ["github"]
    assert "secret_exfiltration" in policy.blocked_tools


def test_mcp_config_yaml_missing_and_non_mapping(tmp_path):
    assert load_mcp_config(tmp_path / "missing.json") == {}
    yaml_config = tmp_path / "mcp.yaml"
    yaml_config.write_text("servers:\n  docs:\n    command: docs\n", encoding="utf-8")
    assert "docs" in load_mcp_config(yaml_config)["servers"]
    list_config = tmp_path / "mcp.json"
    list_config.write_text("[]", encoding="utf-8")
    assert load_mcp_config(list_config) == {}


def test_rewards_and_replay_buffer(tmp_path):
    run = result("ok", True, 0.9)
    assert 0 <= reward_score(run, weights=RewardWeights()) <= 1
    assert cost_efficiency_score(run) > 0.99
    assert tool_usage_quality_score(run) == 1.0
    record = TrajectoryRecord.from_result(generation=1, result=run, reward=0.9)
    buffer = ReplayBuffer(max_size=1)
    buffer.add(record)
    path = buffer.save(tmp_path / "replay.json")
    assert path.exists()
    assert buffer.worst()[0].candidate_id == "ok"


def test_rewards_penalize_provider_errors_and_high_cost():
    run = PromptRunResult(
        candidate=PromptCandidate("err", "Prompt"),
        evaluations=[EvaluationResult("TC-001", False, 0.0, "Error")],
        responses={"TC-001": "Provider error: failed"},
        usage={"total_tokens": 200_000},
    )
    assert tool_usage_quality_score(run) == 0.0
    assert cost_efficiency_score(run) == 0.0
    assert reward_score(run) < 0.5


def test_reflection_mutation_and_inspo_evolution():
    provider = MockProvider()
    failed = PromptRunResult(
        candidate=PromptCandidate("bad", "Prompt"),
        evaluations=[EvaluationResult("TC-001", False, 0.1, "Bad", ["Format"], "format_violation")],
        responses={"TC-001": "Bad"},
    )
    reflection = reflect_failures(failed, provider)
    assert reflection
    child = mutate_instruction(failed, provider, generation=2, child_index=1)
    assert child.id == "generation_2_child_1"
    evolution = run_inspo_evolution(
        task="Отвечай JSON",
        baseline_prompt="Prompt",
        testcases=[case()],
        provider=provider,
        population_size=2,
        generations=1,
    )
    assert evolution.best.candidate.content
    assert evolution.replay_buffer.records
