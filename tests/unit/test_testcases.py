import json

import pytest

from prompt_evolve.config import ConfigError
from prompt_evolve.providers import MockProvider
from prompt_evolve.testcases import (
    dedupe_testcases,
    ensure_target_testcases,
    load_testcases,
    save_testcases,
    self_check_testcases,
    testcase_from_dict,
    validate_testcases,
)


def valid_case(case_id="TC-001", input_text="Input"):
    return {
        "id": case_id,
        "name": "Case",
        "type": "happy_path",
        "priority": "high",
        "input": input_text,
        "expected_behavior": "Expected",
        "evaluation_criteria": ["Criterion one", "Criterion two"],
    }


def test_testcase_from_dict_requires_fields():
    data = valid_case()
    data.pop("input")
    with pytest.raises(ConfigError, match="missing input"):
        testcase_from_dict(data)


def test_validate_requires_criteria_list():
    data = valid_case()
    data["evaluation_criteria"] = "bad"
    with pytest.raises(ConfigError, match="evaluation_criteria"):
        validate_testcases([data])


def test_load_and_save_testcases(tmp_path):
    path = tmp_path / "tests.json"
    path.write_text(json.dumps([valid_case()]), encoding="utf-8")
    cases = load_testcases(path)
    out = save_testcases(cases, tmp_path / "out.json")
    assert json.loads(out.read_text(encoding="utf-8"))[0]["id"] == "TC-001"


def test_load_invalid_json(tmp_path):
    path = tmp_path / "tests.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid tests file format"):
        load_testcases(path)


def test_dedupe_testcases():
    a = testcase_from_dict(valid_case("TC-001", "Same"))
    b = testcase_from_dict(valid_case("TC-002", "Same"))
    assert len(dedupe_testcases([a, b])) == 1


def test_ensure_target_generates_missing():
    cases = ensure_target_testcases("Task", [], MockProvider(), target_tests=3)
    assert len(cases) == 3
    assert cases[0].id == "TC-001"


def test_user_tests_only_does_not_generate():
    existing = [testcase_from_dict(valid_case())]
    cases = ensure_target_testcases("Task", existing, MockProvider(), target_tests=3, user_tests_only=True)
    assert len(cases) == 1


def test_self_check_warnings():
    case = testcase_from_dict({**valid_case(), "evaluation_criteria": ["Only one"]})
    warnings = self_check_testcases([case, case])
    assert any("Duplicate" in item for item in warnings)
    assert any("too few" in item for item in warnings)
