import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
import yaml


WORKFLOW = yaml.safe_load(
    (Path(__file__).parents[1] / "workflows/pr-staging.yml").read_text()
)
JOB = WORKFLOW["jobs"]["deploy-staging"]
STEPS = {step["id"]: step for step in JOB["steps"] if "id" in step}
STAGING = JOB["env"]["STAGING_ENV_ID"]
PRODUCTION = JOB["env"]["PROD_ENV_ID"]
SHA = "b" * 40
IMAGE = f"ghcr.io/johnpooch/diplicity-service:{SHA}"


def execute(step, responses, tmp_path, environment=None, script=None):
    requests = []
    remaining = list(responses)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            requests.append({"path": self.path, "body": json.loads(body)})
            status, result = remaining.pop(0) if remaining else (500, {})
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        def do_GET(self):
            requests.append({"path": self.path, "authorization": self.headers.get("Authorization")})
            status, result = remaining.pop(0) if remaining else (500, {})
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        def do_HEAD(self):
            requests.append({"path": self.path, "authorization": self.headers.get("Authorization")})
            status, result = remaining.pop(0) if remaining else (500, {})
            self.send_response(status)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.server_port}"
    try:
        result = subprocess.run(
            ["bash", "-c", script or STEPS[step]["run"]],
            env={
                **os.environ,
                **JOB["env"],
                "RAILWAY_API_ENDPOINT": endpoint,
                "RAILWAY_ACCOUNT_TOKEN": "test-token",
                "STAGING_URL": endpoint,
                "COMMIT_SHA": SHA,
                "GITHUB_OUTPUT": str(tmp_path / "output"),
                **(environment or {}),
            },
            capture_output=True,
            text=True,
            timeout=10,
        )
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    return result, requests


def service_responses(status="SUCCESS", triggers=None):
    return [
        (200, {"data": {"serviceInstanceUpdate": True}}),
        (
            200,
            {
                "data": {
                    "serviceInstance": {
                        "source": {"image": IMAGE, "repo": None},
                        "service": {"repoTriggers": {"edges": triggers or []}},
                    }
                }
            },
        ),
        (200, {"data": {"serviceInstanceDeployV2": "deployment-id"}}),
        (200, {"data": {"deployment": {"status": status}}}),
    ]


def test_django_succeeds_before_worker_deploys(tmp_path):
    result, requests = execute(
        "railway", service_responses() + service_responses(), tmp_path
    )
    assert result.returncode == 0, result.stderr
    assert len(requests) == 8
    assert requests[0]["body"]["variables"]["serviceId"] == JOB["env"]["DJANGO_SERVICE_ID"]
    assert requests[4]["body"]["variables"]["serviceId"] == JOB["env"]["WORKER_SERVICE_ID"]
    assert requests[3]["body"]["variables"] == {"id": "deployment-id"}
    for request in requests:
        variables = request["body"]["variables"]
        if "environmentId" in variables:
            assert variables["environmentId"] == STAGING
        if "input" in variables:
            assert variables["input"] == {"source": {"image": IMAGE, "repo": None}}


@pytest.mark.parametrize("status", ["FAILED", "CRASHED", "REMOVED", "SKIPPED"])
def test_terminal_django_failure_never_deploys_worker(tmp_path, status):
    result, requests = execute("railway", service_responses(status), tmp_path)
    assert result.returncode != 0
    assert len(requests) == 4
    assert (tmp_path / "output").read_text() == "failure_step=Deploy Django\n"


def test_worker_failure_fails_the_run(tmp_path):
    result, requests = execute(
        "railway", service_responses() + service_responses("FAILED"), tmp_path
    )
    assert result.returncode != 0
    assert len(requests) == 8
    assert (tmp_path / "output").read_text().endswith("failure_step=Deploy worker\n")


@pytest.mark.parametrize(
    "response",
    [
        (200, {"data": {"serviceInstanceDeployV2": None}}),
        (200, {"errors": [{"message": "Not Authorized"}], "data": None}),
        (503, {"data": {"serviceInstanceDeployV2": "must-not-poll"}}),
    ],
)
def test_deploy_errors_never_poll_an_invalid_id(tmp_path, response):
    result, requests = execute("railway", service_responses()[:2] + [response], tmp_path)
    assert result.returncode != 0
    assert len(requests) == 3


@pytest.mark.parametrize(
    "response",
    [
        (200, {"data": {"deployment": None}}),
        (200, {"data": {"deployment": {"status": None}}}),
        (200, {"errors": [{"message": "Deployment not found"}]}),
        (503, {"data": {"deployment": {"status": "SUCCESS"}}}),
    ],
)
def test_failed_lookup_stops_instead_of_polling_again(tmp_path, response):
    result, requests = execute("railway", service_responses()[:3] + [response], tmp_path)
    assert result.returncode != 0
    assert len(requests) == 4


@pytest.mark.parametrize("environment", [PRODUCTION, "some-other-environment", ""])
def test_environment_guard_runs_before_any_railway_request(tmp_path, environment):
    result, requests = execute(
        "railway", [], tmp_path, {"STAGING_ENV_ID": environment}
    )
    assert result.returncode != 0
    assert requests == []


def test_only_staging_repo_triggers_are_deleted(tmp_path):
    triggers = [
        {"node": {"id": "production-trigger", "environmentId": PRODUCTION}},
        {"node": {"id": "staging-trigger", "environmentId": STAGING}},
    ]
    responses = service_responses(triggers=triggers)
    responses.insert(2, (200, {"data": {"deploymentTriggerDelete": True}}))
    result, requests = execute("railway", responses + service_responses(), tmp_path)
    assert result.returncode == 0, result.stderr
    deletes = [
        request for request in requests
        if "deploymentTriggerDelete" in request["body"]["query"]
    ]
    assert len(deletes) == 1
    assert deletes[0]["body"]["variables"] == {"id": "staging-trigger"}


def test_a_repo_source_left_behind_fails_before_deployment(tmp_path):
    responses = service_responses()[:2]
    responses[1][1]["data"]["serviceInstance"]["source"]["repo"] = "johnpooch/diplicity-react"
    result, requests = execute("railway", responses, tmp_path)
    assert result.returncode != 0
    assert len(requests) == 2


def test_overall_deployment_deadline_fails_without_starting_worker(tmp_path):
    script = STEPS["railway"]["run"].replace(
        "DEADLINE=$((SECONDS + 900))", "DEADLINE=$SECONDS"
    )
    result, requests = execute("railway", service_responses()[:3], tmp_path, script=script)
    assert result.returncode != 0
    assert len(requests) == 3
    assert "Timed out waiting for Django" in result.stderr


def test_smoke_test_uses_the_token_and_paginated_count(tmp_path):
    result, requests = execute(
        "smoke", [(200, {"accessToken": "login-token"}), (200, {"count": 12, "results": []})], tmp_path
    )
    assert result.returncode == 0, result.stderr
    assert requests[0]["body"] == {"email": "test-user@example.com", "password": "password"}
    assert requests[1]["path"] == "/games/?mine=true"
    assert requests[1]["authorization"] == "Bearer login-token"


@pytest.mark.parametrize("login", [{}, {"accessToken": None}, {"accessToken": ""}])
def test_smoke_test_requires_an_access_token(tmp_path, login):
    result, requests = execute("smoke", [(200, login)], tmp_path)
    assert result.returncode != 0
    assert len(requests) == 1


@pytest.mark.parametrize("games", [{"count": 0}, {"results": [{"id": 1}]}, {"count": "1"}])
def test_smoke_test_requires_a_positive_numeric_count(tmp_path, games):
    result, requests = execute(
        "smoke", [(200, {"accessToken": "login-token"}), (200, games)], tmp_path
    )
    assert result.returncode != 0
    assert len(requests) == 2


@pytest.mark.parametrize("status", [401, 403, 500])
def test_smoke_test_rejects_http_errors_even_with_valid_json(tmp_path, status):
    result, requests = execute("smoke", [(status, {"accessToken": "login-token"})], tmp_path)
    assert result.returncode != 0
    assert len(requests) == 1


@pytest.mark.parametrize(
    "responses, expected",
    [
        ([(403, {})], 1),
        ([(200, {"token": "anonymous-token"}), (403, {})], 2),
        ([(200, {"token": "anonymous-token"}), (200, {})], 2),
    ],
)
def test_public_image_access_never_uses_registry_credentials(tmp_path, responses, expected):
    script = STEPS["visibility"]["run"].replace("https://ghcr.io", "$RAILWAY_API_ENDPOINT")
    script = script.replace(
        "'$RAILWAY_API_ENDPOINT/token?scope=repository:johnpooch/diplicity-service:pull&service=ghcr.io'",
        '"$RAILWAY_API_ENDPOINT/token?scope=repository:johnpooch/diplicity-service:pull&service=ghcr.io"',
    )
    result, requests = execute("visibility", responses, tmp_path, script=script)
    assert len(requests) == expected
    assert (result.returncode == 0) == (responses[-1][0] == 200)
    if result.returncode != 0:
        assert "John must" in result.stderr
    if len(requests) == 2:
        assert requests[1]["authorization"] == "Bearer anonymous-token"


def test_failed_build_cannot_reach_railway():
    identifiers = list(STEPS)
    assert identifiers.index("build") < identifiers.index("visibility") < identifiers.index("railway")
    assert "if" not in STEPS["railway"]
    assert "RAILWAY_ACCOUNT_TOKEN" not in JOB["env"]
    assert "concurrency" not in WORKFLOW
    assert JOB["concurrency"] == {"group": "staging", "cancel-in-progress": False}
    assert "contains(github.event.pull_request.labels.*.name, 'deploy-to-staging')" in JOB["if"]


def test_shell_scripts_never_interpolate_github_expressions():
    for step in JOB["steps"]:
        if "run" in step:
            assert "${{" not in step["run"]
            result = subprocess.run(
                ["bash", "-n"], input=step["run"], capture_output=True, text=True
            )
            assert result.returncode == 0, result.stderr
