from pants.engine.rules import collect_rules
from pants.engine.unions import UnionRule
from dataclasses import dataclass
from pants.engine.target import Dependencies, Sources, Target, Tags
from pants.core.goals.package import OutputPathField, PackageFieldSet


@dataclass(frozen=True)
class DockerImageFieldSet(PackageFieldSet):
    required_fields = (Sources,)
    sources: Sources

def rules():
    return [
        *collect_rules(),
        UnionRule(PackageFieldSet, DockerImageFieldSet)
    ]


class DockerTarget(Target):
    alias = "docker"
    core_fields = (Sources, Dependencies, Tags)

    
