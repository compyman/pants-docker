from dataclasses import dataclass

import pytest
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.backend.python.goals import pytest_runner
from pants.backend.python.target_types import PythonLibrary, PythonTests
from pants.backend.python.util_rules import pex_from_targets
from pants.core.target_types import RelocatedFiles, RelocatedFilesSources
from pants.engine.addresses import Address
from pants.engine.fs import Snapshot
from pants.engine.rules import rule, UnionRule
from pants.testutil.rule_runner import QueryRule, RuleRunner
from pants.engine.target import FieldSet
from sendwave.pants_docker.sources import (DockerComponent,
                                           DockerComponentRequest)


@dataclass(frozen=True)
class DockerRelocatedFiles(FieldSet):
    required_fields = (RelocatedFilesSources,)
    sources: RelocatedFilesSources


class DockerRelocatedFilesRequest(DockerComponentRequest):
    field_set_type = DockerRelocatedFiles


@rule
async def get_relocated_files(req: DockerRelocatedFiles) -> DockerComponent:
    sources = await Get(
        SourceFiles,
        SourceFilesRequest,
        SourceFilesRequest(
            sources_fields=[req.fs.sources], for_sources_types=[RelocatedFilesSources]
        ),
    )
    logger.info("relocated_files  %s", ",".join(sources.snapshot.files))
    return DockerComponent(
        commands=(),
        sources=sources.snapshot.digest,
    )


@pytest.fixture
def rule_runner() -> RuleRunner:
    rule_runner = RuleRunner(
        target_types=[RelocatedFiles],
        rules=[
            *pytest_runner.rules(),
            *pex_from_targets.rules(),
            UnionRule(DockerComponentRequest, DockerRelocatedFilesRequest),
            QueryRule(DockerComponent, [DockerRelocatedFilesRequest]),
        ],
    )
    BUILD = (
        "files(name='to-move', sources=['move_me.txt'])\n"
        "relocated_files(name='moved', files_targets=[':to-move'], src='./', dest='moved-now/')"
    )
    rule_runner.write_files(
        {
            "app/move_me.txt": "",
            "app/BUILD": BUILD,
        }
    )

    return rule_runner


def test_get_relocated_files(rule_runner: RuleRunner) -> None:
    t = relocated_runner.get_target(address=Address("app", target_name="moved"))
    print(t)
    x = relocated_runner.request(
        DockerComponent, [DockerRelocatedFilesRequest(DockerRelocatedFiles.create(t))]
    )
    print(x)
    snap = relocated_runner.request(Snapshot, [x.sources])
    print(snap)
    assert snap.files == ("app/resources.txt",)
