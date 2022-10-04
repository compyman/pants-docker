import logging
from dataclasses import dataclass
from typing import Any, Optional

from pants.backend.python.subsystems.repos import PythonRepos
from pants.backend.python.subsystems.setup import PythonSetup
from pants.backend.python.target_types import PythonRequirementsField
from pants.core.util_rules.system_binaries import BinaryPathRequest, BinaryPaths
from pants.engine.fs import Digest, GlobMatchErrorBehavior, PathGlobs
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import FieldSet
from pants.engine.unions import UnionRule
from pants.option.global_options import BootstrapOptions
from sendwave.pants_docker.docker_component import (
    DockerComponent,
    DockerComponentFieldSet,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VirtualEnvRequest:
    enable_resolves: bool
    requirement_constraints: Optional[str]


@rule
async def create_virtual_env(
    resolve_request: VirtualEnvRequest,
) -> DockerComponent:
    assert (
        not resolve_request.enable_resolves
    ), "Pants lockfiles not yet supported"

    copy_command = []
    sources = None
    pip_upgrade_constraint = ""
    if constraint_file := resolve_request.requirement_constraints:

        sources = await Get(
            Digest,
            PathGlobs(
                [constraint_file],
                glob_match_error_behavior=GlobMatchErrorBehavior.error,
                description_of_origin="the option `requirement_constraints`",
            ),
        )
        pip_upgrade_constraint = " -c {}".format(constraint_file)
        copy_command.append("COPY application/{} .\n".format(constraint_file))
    return DockerComponent(
        commands=tuple(
            [
                *copy_command,
                "RUN python -m venv --upgrade /.virtual_env\n",
                "ENV PATH=/.virtual_env/bin:$PATH\n",
                "ENV VIRTUAL_ENV=/.virtual_env\n",
                "RUN python -m pip install --upgrade pip{}\n".format(
                    pip_upgrade_constraint
                ),
            ]
        ),
        sources=sources,
    )


@dataclass(frozen=True)
class PythonRequirementsFS(FieldSet):
    required_fields = (PythonRequirementsField,)
    requirements: PythonRequirementsField


@rule
async def get_requirements(
    field_set: PythonRequirementsFS, setup: PythonSetup, repos: PythonRepos
) -> DockerComponent:
    assert not setup.enable_resolves, "Pants lockfiles not yet supported"
    if repos.repos:
        links_args = " ".join(
            "--find-links {}".format(repo for repo in repos.repos)
        )
    else:
        links_args = ""
    num_indices = len(repos.indexes)
    if num_indices >= 1:
        index_args = f"--index-url {repos.indexes[0]} "
    if num_indices > 1:
        index_args = index_args + " ".join(
            [f"--extra-index-url {url}" for url in repos.indexes[1:]]
        )
    if num_indices == 0:
        index_args = " --no-index "
    constraint_arg = ""
    if setup.requirement_constraints:
        constraint_arg = f"--constraint {setup.requirement_constraints}"

    commands = tuple(
        "RUN python -m pip install {} {} {} {}\n".format(
            index_args, links_args, constraint_arg, lib
        )
        for lib in field_set.requirements.value
    )
    return DockerComponent(
        commands=commands,
        sources=None,
    )


def rules():
    return [
        UnionRule(DockerComponentFieldSet, PythonRequirementsFS),
        *collect_rules(),
    ]
