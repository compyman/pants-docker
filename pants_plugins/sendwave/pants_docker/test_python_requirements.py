import pytest
from pants.engine.fs import Digest, PathGlobs
from pants.engine.internals.scheduler import ExecutionError
from pants.testutil.rule_runner import QueryRule, RuleRunner
from sendwave.pants_docker.docker_component import DockerComponent
from sendwave.pants_docker.python_requirement import (
    VirtualEnvRequest,
    create_virtual_env,
    rules,
)


@pytest.fixture
def rule_runner():
    runner = RuleRunner(
        rules=[
            create_virtual_env,
            QueryRule(DockerComponent, [VirtualEnvRequest]),
        ]
    )
    runner.write_files({"faux_constraints.txt": "pytest==1"})
    return runner


def test_enable_resolve_execution_errors(rule_runner):
    request = VirtualEnvRequest(
        enable_resolves=True, requirement_constraints=None
    )
    with pytest.raises(ExecutionError):
        rule_runner.request(DockerComponent, [request])


def test_gets_constraints_execution_error_does_not_exist(rule_runner):
    request = VirtualEnvRequest(
        enable_resolves=False, requirement_constraints="fake_constraints.txt"
    )
    with pytest.raises(ExecutionError):
        result = rule_runner.request(DockerComponent, [request])


def test_create_virtual_env_no_constraints(rule_runner):
    request = VirtualEnvRequest(
        enable_resolves=False, requirement_constraints=None
    )
    print(request)
    result = rule_runner.request(DockerComponent, [request])
    assert result.commands == (
        "RUN python -m venv --upgrade /.virtual_env\n",
        "ENV PATH=/.virtual_env/bin:$PATH\n",
        "ENV VIRTUAL_ENV=/.virtual_env\n",
        "RUN python -m pip install --upgrade pip\n",
    )
    assert result.sources is None


def test_create_virtual_env_with_constraints(rule_runner):
    request = VirtualEnvRequest(
        enable_resolves=False, requirement_constraints="faux_constraints.txt"
    )
    result = rule_runner.request(DockerComponent, [request])
    assert result.commands == (
        "COPY application/faux_constraints.txt .\n",
        "RUN python -m venv --upgrade /.virtual_env\n",
        "ENV PATH=/.virtual_env/bin:$PATH\n",
        "ENV VIRTUAL_ENV=/.virtual_env\n",
        "RUN python -m pip install --upgrade pip\n",
    )
    assert isinstance(result.sources, Digest)
