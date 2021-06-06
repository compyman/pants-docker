from abc import ABC
from dataclasses import dataclass
from typing import Tuple, ClassVar, Type

from pants.engine.target import FieldSet, Targets
from pants.engine.unions import union, UnionMembership
from pants.engine.fs import Digest
from pants.core.target_types import Sources, RelocatedFilesSources, FilesSources
from pants.core.util_rules.stripped_source_files import StrippedSourceFiles
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.rules import Get
from pants.backend.python.target_types import PythonRequirementsField, PythonRequirementsFileSources, PythonLibrarySources
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DockerComponent():
    commands: Tuple[str]
    sources: Digest
    order: int = 0


@union
class DockerComponentRequest(ABC):
    field_set_type: ClassVar[Type[FieldSet]]
    fs: FieldSet

    def __init__(self, field_set) -> None:
        self.fs = field_set


async def from_dependencies(ts: Targets,
                      um: UnionMembership) -> Tuple[DockerComponentRequest]:
    return [request_type(request_type.field_set_type.create(t))
            for t in ts
            for request_type in um[DockerComponentRequest]
            if request_type.field_set_type.is_applicable(t)]
