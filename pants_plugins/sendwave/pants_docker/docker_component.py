import logging
from abc import ABC
from dataclasses import dataclass
from typing import ClassVar, List, Tuple, Type

from pants.engine.fs import Digest
from pants.engine.target import FieldSet, Targets
from pants.engine.unions import UnionMembership, union

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DockerComponent:
    commands: Tuple[str, ...]
    sources: Digest
    order: int = 0


@union
class DockerComponentRequest(ABC):
    field_set_type: ClassVar[Type[FieldSet]]
    fs: FieldSet

    def __init__(self, field_set) -> None:
        self.fs = field_set


def from_dependencies(
    tgts: Targets, um: UnionMembership
) -> List[DockerComponentRequest]:
    return [
        request_type(request_type.field_set_type.create(tgt))
        for tgt in tgts
        for request_type in um[DockerComponentRequest]
        if request_type.field_set_type.is_applicable(tgt)
    ]
