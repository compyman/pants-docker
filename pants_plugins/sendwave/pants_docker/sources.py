from dataclasses import dataclass
from pants.engine.unions import UnionRule
from pants.engine.rules import collect_rules, rule, Get
from pants.core.util_rules.stripped_source_files import StrippedSourceFiles
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.target import Sources, FieldSet

from sendwave.pants_docker.docker_component import DockerComponentRequest, DockerComponent


@dataclass(frozen=True)
class DockerSources(FieldSet):
    required_fields = (Sources,)
    sources: Sources

class SourceDockerComponentRequest(DockerComponentRequest):
    field_set_type = DockerSources



@rule
async def get_sources(req: SourceDockerComponentRequest) -> DockerComponent:
    source_files = await Get(StrippedSourceFiles,
                             SourceFilesRequest([req.fs.sources]))
    return DockerComponent(        
        commands=(),
        sources=source_files.snapshot)


def rules():
    return [UnionRule(DockerComponentRequest, SourceDockerComponentRequest),
            *collect_rules()]
