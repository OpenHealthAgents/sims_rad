"""
Kestra Flow Schema & Syntax Validation Tests.
Validates all flows in kestra/flows/ against Kestra flow and task specification standards.
"""
from pathlib import Path
import re
from typing import Any, Dict, List
import pytest
import yaml

FLOWS_DIR = Path("kestra/flows")

VALID_TASK_TYPES = {
    "io.kestra.plugin.core.http.Request",
    "io.kestra.plugin.core.log.Log",
    "io.kestra.plugin.core.flow.If",
    "io.kestra.plugin.core.flow.Parallel",
    "io.kestra.plugin.core.flow.EachSequential",
    "io.kestra.plugin.core.debug.Return",
    "io.kestra.plugin.core.execution.Fail",
}

VALID_TRIGGER_TYPES = {
    "io.kestra.plugin.core.trigger.Schedule",
    "io.kestra.plugin.core.trigger.Webhook",
}

ISO8601_DURATION_PATTERN = r"^PT(?:\d+H)?(?:\d+M)?(?:\d+(?:\.\d+)?S)?$"
CRON_PATTERN = r"^(\*|([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])|\*\/[0-9]+)\s+(\*|([0-9]|1[0-9]|2[0-3])|\*\/[0-9]+)\s+(\*|([1-9]|1[0-9]|2[0-9]|3[0-1])|\*\/[0-9]+)\s+(\*|([1-9]|1[0-2])|\*\/[0-9]+)\s+(\*|([0-6])|\*\/[0-9]+)$"


def get_all_flow_files() -> List[Path]:
    return list(FLOWS_DIR.glob("*.yml")) + list(FLOWS_DIR.glob("*.yaml"))


def validate_task_definition(task: Dict[str, Any], flow_id: str) -> None:
    assert "id" in task, f"Task in flow '{flow_id}' missing 'id'"
    assert "type" in task, f"Task '{task['id']}' in flow '{flow_id}' missing 'type'"
    assert task["type"] in VALID_TASK_TYPES, f"Unknown task type '{task['type']}' in flow '{flow_id}'"

    # HTTP Request specific validation
    if task["type"] == "io.kestra.plugin.core.http.Request":
        assert "uri" in task, f"HTTP task '{task['id']}' missing 'uri'"
        assert "method" in task, f"HTTP task '{task['id']}' missing 'method'"
        assert task["method"] in ("GET", "POST", "PUT", "DELETE", "PATCH")

        # Retry schema validation if present
        if "retry" in task:
            retry = task["retry"]
            assert "type" in retry, f"Retry in task '{task['id']}' missing 'type'"
            assert retry["type"] in ("exponential", "constant", "random")
            assert "maxAttempts" in retry, f"Retry in task '{task['id']}' missing 'maxAttempts'"
            assert isinstance(retry["maxAttempts"], int) and retry["maxAttempts"] > 0
            if "interval" in retry:
                assert re.match(ISO8601_DURATION_PATTERN, retry["interval"], re.IGNORECASE), (
                    f"Invalid ISO-8601 interval '{retry['interval']}' in task '{task['id']}'"
                )

    # Log task validation
    elif task["type"] == "io.kestra.plugin.core.log.Log":
        assert "message" in task, f"Log task '{task['id']}' missing 'message'"

    # If branch task validation
    elif task["type"] == "io.kestra.plugin.core.flow.If":
        assert "condition" in task, f"If task '{task['id']}' missing 'condition'"
        assert "then" in task, f"If task '{task['id']}' missing 'then' branch"
        assert isinstance(task["then"], list)
        for sub_task in task["then"]:
            validate_task_definition(sub_task, flow_id)
        if "else" in task:
            assert isinstance(task["else"], list)
            for sub_task in task["else"]:
                validate_task_definition(sub_task, flow_id)


def validate_trigger_definition(trigger: Dict[str, Any], flow_id: str) -> None:
    assert "id" in trigger, f"Trigger in flow '{flow_id}' missing 'id'"
    assert "type" in trigger, f"Trigger '{trigger['id']}' in flow '{flow_id}' missing 'type'"
    assert trigger["type"] in VALID_TRIGGER_TYPES, f"Unknown trigger type '{trigger['type']}' in flow '{flow_id}'"

    if trigger["type"] == "io.kestra.plugin.core.trigger.Schedule":
        assert "cron" in trigger, f"Schedule trigger '{trigger['id']}' missing 'cron'"
        # Standard 5-field cron check
        fields = trigger["cron"].strip().split()
        assert len(fields) == 5, f"Invalid cron expression '{trigger['cron']}' in trigger '{trigger['id']}'"
    elif trigger["type"] == "io.kestra.plugin.core.trigger.Webhook":
        assert "key" in trigger, f"Webhook trigger '{trigger['id']}' missing 'key'"


@pytest.mark.parametrize("flow_path", get_all_flow_files(), ids=lambda p: p.name)
def test_kestra_flow_yaml_syntax_and_schema(flow_path: Path):
    """Ensure every flow file parses cleanly as valid YAML and conforms to Kestra schema."""
    with open(flow_path, "r", encoding="utf-8") as f:
        content = f.read()

    flow = yaml.safe_load(content)
    assert isinstance(flow, dict), f"Flow file '{flow_path.name}' must contain a YAML mapping"

    # Required top-level attributes
    assert "id" in flow, f"Flow '{flow_path.name}' missing 'id'"
    assert "namespace" in flow, f"Flow '{flow_path.name}' missing 'namespace'"
    assert flow["namespace"] == "sims.radiology", f"Flow '{flow_path.name}' has unexpected namespace"
    assert "tasks" in flow, f"Flow '{flow_path.name}' missing 'tasks'"
    assert isinstance(flow["tasks"], list) and len(flow["tasks"]) > 0

    # Validate all tasks
    for task in flow["tasks"]:
        validate_task_definition(task, flow["id"])

    # Validate triggers if present
    if "triggers" in flow:
        assert isinstance(flow["triggers"], list)
        for trigger in flow["triggers"]:
            validate_trigger_definition(trigger, flow["id"])


def test_required_kestra_flows_exist():
    """Verify all 3 required Kestra flows are present."""
    required_flows = [
        "study_ingestion_pipeline.yml",
        "report_delivery_retry.yml",
        "sla_monitor_pipeline.yml",
    ]
    for rf in required_flows:
        path = FLOWS_DIR / rf
        assert path.exists(), f"Required Kestra flow '{rf}' not found in '{FLOWS_DIR}'"
