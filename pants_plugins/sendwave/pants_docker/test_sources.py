import pytest
from pants.backend.python.goals import pytest_runner
from pants.backend.python.goals.pytest_runner import PythonTestFieldSet
from pants.backend.python.target_types import (PythonLibrary, PythonSources,
                                               PythonTests)
from pants.backend.python.util_rules import pex_from_targets
from pants.core.goals.test import TestResult
from pants.core.target_types import Files, RelocatedFiles, Resources
from pants.engine.addresses import Address
from pants.engine.fs import (AddPrefix, CreateDigest, Digest, FileContent,
                             MergeDigests, PathGlobs, Snapshot)
from pants.engine.rules import rule
from pants.testutil.rule_runner import QueryRule, RuleRunner
from sendwave.pants_docker.sources import (DockerComponent,
                                           DockerComponentRequest, DockerFiles,
                                           DockerFilesRequest,
                                           DockerPythonSources,
                                           DockerPythonSourcesRequest,
                                           DockerResources,
                                           DockerResourcesRequest, rules)


@pytest.fixture
def rule_runner() -> RuleRunner:
    rule_runner = RuleRunner(
        target_types=[PythonLibrary, PythonTests, Files, Resources, RelocatedFiles],
        rules=[
            *pytest_runner.rules(),
            *pex_from_targets.rules(),
            *rules(),
            QueryRule(DockerComponent, [DockerPythonSourcesRequest]),
            QueryRule(DockerComponent, [DockerFilesRequest]),
            QueryRule(DockerComponent, [DockerResourcesRequest]),
        ],
    )
    return rule_runner


@pytest.fixture
def sources_runner(rule_runner: RuleRunner) -> RuleRunner:
    """construct rule runner environment with targets containing various
    'Sources' types."""
    build = (
        "python_library()\n"
        "files(name='file', sources=['test.txt'])\n"
        "resources(name='resources', sources=['resources.txt'])"
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
    x = sources_runner.request(
        DockerComponent, [DockerPythonSourcesRequest(DockerPythonSources.create(t))]
    )
    snap = sources_runner.request(Snapshot, [x.sources])
    assert snap.files == ("app/test.py",)


def test_get_files(sources_runner: RuleRunner) -> None:
    t = sources_runner.get_target(address=Address("app", target_name="file"))
    x = sources_runner.request(
        DockerComponent, [DockerFilesRequest(DockerFiles.create(t))]
    )
    snap = sources_runner.request(Snapshot, [x.sources])
    assert snap.files == ("app/test.txt",)


def test_get_resources(sources_runner: RuleRunner) -> None:
    t = sources_runner.get_target(address=Address("app", target_name="resources"))
    x = sources_runner.request(
        DockerComponent, [DockerResourcesRequest(DockerResources.create(t))]
    )
    snap = sources_runner.request(Snapshot, [x.sources])
    assert snap.files == ("app/resources.txt",)
