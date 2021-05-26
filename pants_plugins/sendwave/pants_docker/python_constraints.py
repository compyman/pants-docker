from dataclasses import dataclass
from typing import Optional

from pants.engine.rules import collect_rules, rule, Get
from pants.engine.fs import (CreateDigest, Digest, FileContent, PathGlobs)


@dataclass(frozen=True)
class ConstraintsDigest:
    file_name: str
    digest: Digest


@dataclass(frozen=True)
class ConstraintsRequest:
    file_name: Optional[str]


@rule
async def get_constraints(req: ConstraintsRequest) -> ConstraintsDigest:
    file_name = req.file_name
    if file_name is not None:
        digest = await Get(
            Digest, PathGlobs([file_name])
        )
    else:
        file_name = "dummy.txt"
        digest = await Get(Digest, CreateDigest([FileContent(file_name, b"")]))
    return ConstraintsDigest(file_name, digest)




def rules():
    return collect_rules()
