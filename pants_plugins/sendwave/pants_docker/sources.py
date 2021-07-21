from dataclasses import dataclass

from pants.backend.python.target_types import PythonSources
from pants.core.target_types import FilesSources, ResourcesSources
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.core.util_rules.stripped_source_files import StrippedSourceFiles
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import FieldSet, Sources
from pants.engine.unions import UnionRule
from sendwave.pants_docker.docker_component import (DockerComponent,
                                                    DockerComponentFieldSet)


@dataclass(frozen=True)
class DockerFilesFS(FieldSet):
    required_fields = (FilesSources,)
    sources: FilesSources


@rule
async def get_files(field_set: DockerFilesFS) -> DockerComponent:
    return DockerComponent(
        commands=(),
        sources=(
            await Get(StrippedSourceFiles, SourceFilesRequest([field_set.sources]))
        ).snapshot.digest,
    )


@dataclass(frozen=True)
class DockerResourcesFS(FieldSet):
    required_fields = (ResourcesSources,)
    sources: ResourcesSources


@rule
async def get_resources(field_set: DockerResourcesFS) -> DockerComponent:
    return DockerComponent(
        commands=(),
        sources=(
            await Get(StrippedSourceFiles, SourceFilesRequest([field_set.sources]))
        ).snapshot.digest,
    )


@dataclass(frozen=True)
class DockerPythonSourcesFS(FieldSet):
    required_fields = (PythonSources,)
    sources: PythonSources


@rule
async def get_sources(field_set: DockerPythonSourcesFS) -> DockerComponent:
    source_files = await Get(StrippedSourceFiles, SourceFilesRequest([field_set.sources]))
    return DockerComponent(commands=(), sources=source_files.snapshot.digest)


def rules():
    return [
        UnionRule(DockerComponentFieldSet, DockerPythonSourcesFS),
        UnionRule(DockerComponentFieldSet, DockerResourcesFS),
        UnionRule(DockerComponentFieldSet, DockerFilesFS),
        *collect_rules(),
    ]
