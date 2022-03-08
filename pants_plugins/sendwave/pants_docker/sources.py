import logging
from dataclasses import dataclass

from pants.backend.python.target_types import PythonSourceField
from pants.core.target_types import (FileSourceField, RelocatedFilesSourcesField,
                                     ResourceSourceField)
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.core.util_rules.stripped_source_files import StrippedSourceFiles
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import FieldSet
from pants.engine.unions import UnionRule
from sendwave.pants_docker.docker_component import (DockerComponent,
                                                    DockerComponentFieldSet)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DockerRelocatedFilesFS(FieldSet):
    required_fields = (RelocatedFilesSourcesField,)
    sources: RelocatedFilesSourcesField


@rule
async def get_relocated_files(field_set: DockerRelocatedFilesFS) -> DockerComponent:
    return DockerComponent(
        commands=(),
        sources=(
            await Get(
                StrippedSourceFiles,
                SourceFilesRequest,
                SourceFilesRequest(
                    sources_fields=[field_set.sources],
                    for_sources_types=[FileSourceField],
                    enable_codegen=True,
                ),
            )
        ).snapshot.digest,
    )


@dataclass(frozen=True)
class DockerFilesFS(FieldSet):
    required_fields = (FileSourceField,)
    sources: FileSourceField


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
    required_fields = (ResourceSourceField,)
    sources: ResourceSourceField


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
    required_fields = (PythonSourceField,)
    sources: PythonSourceField


@rule
async def get_sources(field_set: DockerPythonSourcesFS) -> DockerComponent:
    source_files = await Get(
        StrippedSourceFiles, SourceFilesRequest([field_set.sources])
    )
    return DockerComponent(commands=(), sources=source_files.snapshot.digest)


def rules():
    return [
        UnionRule(DockerComponentFieldSet, DockerPythonSourcesFS),
        UnionRule(DockerComponentFieldSet, DockerResourcesFS),
        UnionRule(DockerComponentFieldSet, DockerFilesFS),
        UnionRule(DockerComponentFieldSet, DockerRelocatedFilesFS),
        *collect_rules(),
    ]
