import logging
from dataclasses import dataclass
from typing import Tuple

from pants.engine.fs import Digest
from pants.engine.unions import union

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DockerComponent:
    commands: Tuple[str, ...]
    sources: Digest
    order: int = 0


@union
class DockerComponentFieldSet:
    pass
