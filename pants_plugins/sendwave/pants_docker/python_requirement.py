from dataclasses import dataclass

from pants.backend.python.target_types import (PythonRequirementsField,
                                               PythonRequirementsFileSourcesField)
from pants.engine.fs import Digest, PathGlobs
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import FieldSet
from pants.engine.unions import UnionRule
from pants.backend.python.subsystems.repos import PythonRepos
from pants.backend.python.subsystems.setup import PythonSetup
from sendwave.pants_docker.docker_component import (DockerComponent,
                                                    DockerComponentFieldSet)


@dataclass(frozen=True)
class PythonRequirementsFileFS(FieldSet):
    required_fields = (PythonRequirementsFileSourcesField,)
    requirement_file: PythonRequirementsFileSourcesField


_REQUIREMENT_FILE_ORDER = -10


@rule
async def get_requirement_file_component(
    _: PythonRequirementsFileFS, python_setup: PythonSetup
) -> DockerComponent:
    sources = None
    copy_command = []
    if python_setup.requirement_constraints:
        sources = await Get(Digest, PathGlobs([python_setup.requirement_constraints]))
        copy_command.append(
            "COPY application/{} .\n".format(python_setup.requirement_constraints)
        )
    return DockerComponent(
        order=_REQUIREMENT_FILE_ORDER,
        commands=tuple(
            [
                *copy_command,
                "RUN python -m venv --upgrade /.virtual_env\n",
                "ENV PATH=/.virtual_env/bin:$PATH\n",
                "ENV VIRTUAL_ENV=/.virtual_env\n",
                "RUN python -m pip install --upgrade pip\n",
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
    if repos.repos:
        links_args = " ".join("--find-links {}".format(repo for repo in repos.repos))
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
        # This has to go _after we've created & activated the venv.
        order=1 + _REQUIREMENT_FILE_ORDER,
        commands=commands,
        sources=None,
    )


def rules():
    return [
        UnionRule(DockerComponentFieldSet, PythonRequirementsFS),
        UnionRule(DockerComponentFieldSet, PythonRequirementsFileFS),
        *collect_rules(),
    ]
