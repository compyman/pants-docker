from dataclasses import dataclass

from pants.backend.python.target_types import PythonSources
from pants.core.target_types import FilesSources, ResourcesSources
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.core.util_rules.stripped_source_files import StrippedSourceFiles
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import FieldSet, Sources
from pants.engine.unions import UnionRule
from sendwave.pants_docker.docker_component import (DockerComponent,
                                                    DockerComponentRequest)


@dataclass(frozen=True)
class DockerFiles(FieldSet):
    required_fields = (FilesSources,)
    sources: FilesSources


class DockerFilesRequest(DockerComponentRequest):
    field_set_type = DockerFiles


@rule
async def get_files(req: DockerFilesRequest) -> DockerComponent:
    return DockerComponent(
        commands=(),
        sources=(
            await Get(StrippedSourceFiles, SourceFilesRequest([req.fs.sources]))
        ).snapshot.digest,
    )


@dataclass(frozen=True)
class DockerResources(FieldSet):
    required_fields = (ResourcesSources,)
    sources: ResourcesSources


class DockerResourcesRequest(DockerComponentRequest):
    field_set_type = DockerResources


@rule
async def get_resources(req: DockerResourcesRequest) -> DockerComponent:
    return DockerComponent(
        commands=(),
        sources=(
            await Get(StrippedSourceFiles, SourceFilesRequest([req.fs.sources]))
        ).snapshot.digest,
    )


@dataclass(frozen=True)
class DockerPythonSources(FieldSet):
    required_fields = (PythonSources,)
    sources: PythonSources


class DockerPythonSourcesRequest(DockerComponentRequest):
    field_set_type = DockerPythonSources


@rule
async def get_sources(req: DockerPythonSourcesRequest) -> DockerComponent:
    source_files = await Get(StrippedSourceFiles, SourceFilesRequest([req.fs.sources]))
    return DockerComponent(commands=(), sources=source_files.snapshot.digest)


def rules():
    return [
        UnionRule(DockerComponentRequest, DockerPythonSourcesRequest),
        UnionRule(DockerComponentRequest, DockerResourcesRequest),
        UnionRule(DockerComponentRequest, DockerFilesRequest),
        *collect_rules(),
    ]
