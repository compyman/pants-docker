from abc import ABC
from dataclasses import dataclass
from typing import Tuple, ClassVar, Type

from pants.engine.target import FieldSet, Targets
from pants.engine.unions import union, UnionMembership
from pants.engine.fs import Snapshot



@dataclass(frozen=True)
class DockerComponent():
    commands: Tuple[str]
    sources: Snapshot


@union
class DockerComponentRequest(ABC):
    field_set_type: ClassVar[Type[FieldSet]]
    fs: FieldSet

    def __init__(self, field_set) -> None:
        self.fs = field_set


def from_dependencies(ts: Targets,
                      um: UnionMembership) -> Tuple[DockerComponentRequest]:
    return tuple(request_type(request_type.field_set_type.create(t))
                 for t in ts
                 for request_type in um[DockerComponentRequest]
                 if request_type.field_set_type.is_applicable(t))
