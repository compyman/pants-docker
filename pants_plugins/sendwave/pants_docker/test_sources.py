import pytest
from pants.backend.python.target_types import (PythonSourcesGeneratorTarget,
                                               PythonSourceTarget,
                                               PythonTestTarget)
from pants.backend.python.util_rules import pex_from_targets
from pants.core.target_types import FileTarget, ResourceTarget
from pants.engine.addresses import Address
from pants.engine.fs import Snapshot
from pants.testutil.rule_runner import QueryRule, RuleRunner
from sendwave.pants_docker.docker_component import DockerComponent
from sendwave.pants_docker.sources import (DockerFilesFS,
                                           DockerPythonSourcesFS,
                                           DockerRelocatedFilesFS,
                                           DockerResourcesFS, rules)


@pytest.fixture
def rule_runner() -> RuleRunner:
    rule_runner = RuleRunner(
        target_types=[
            PythonSourcesGeneratorTarget,
            PythonSourceTarget,
            FileTarget,
            ResourceTarget,
        ],
        rules=[
            *pex_from_targets.rules(),
            *rules(),
            QueryRule(DockerComponent, [DockerPythonSourcesFS]),
            QueryRule(DockerComponent, [DockerFilesFS]),
            QueryRule(DockerComponent, [DockerResourcesFS]),
            QueryRule(DockerComponent, [DockerRelocatedFilesFS]),
        ],
    )
    return rule_runner


@pytest.fixture
def sources_runner(rule_runner: RuleRunner) -> RuleRunner:
    """construct rule runner environment with targets containing various
    'Sources' types."""
    build = (
        "python_source(source='test.py')\n"
        "file(name='file', source='test.txt')\n"
        "resource(name='resources', source='resources.txt')"
    )
    rule_runner.write_files(
        {
            "app/test.txt": "test_text",
            "app/resources.txt": "resources",
            "app/test.py": "",
            "app/BUILD": build,
        }
    )
    return rule_runner


def test_get_python_sources(sources_runner: RuleRunner) -> None:
    t = sources_runner.get_target(address=Address("app", target_name=""))
    x = sources_runner.request(DockerComponent, [DockerPythonSourcesFS.create(t)])
    snap = sources_runner.request(Snapshot, [x.sources])
    assert snap.files == ("app/test.py",)


def test_get_files(sources_runner: RuleRunner) -> None:
    t = sources_runner.get_target(address=Address("app", target_name="file"))
    x = sources_runner.request(DockerComponent, [DockerFilesFS.create(t)])
    snap = sources_runner.request(Snapshot, [x.sources])
    assert snap.files == ("app/test.txt",)


def test_get_resources(sources_runner: RuleRunner) -> None:
    t = sources_runner.get_target(address=Address("app", target_name="resources"))
    x = sources_runner.request(DockerComponent, [DockerResourcesFS.create(t)])
    snap = sources_runner.request(Snapshot, [x.sources])
    assert snap.files == ("app/resources.txt",)
