from dataclasses import dataclass

from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.unions import UnionRule
from pants.engine.rules import collect_rules, rule, Get
from pants.engine.fs import (Digest, PathGlobs)
from pants.engine.target import FieldSet
from pants.backend.python.target_types import PythonRequirementsField, PythonRequirementsFileSources
from pants.python.python_setup import PythonSetup
from pants.python.python_repos import PythonRepos

from sendwave.pants_docker.docker_component import DockerComponentRequest, DockerComponent

@dataclass(frozen=True)
class PythonRequirementsFile(FieldSet):
    required_fields = (PythonRequirementsFileSources,)
    requirement_file: PythonRequirementsFileSources

class PythonRequirementsFileRequest(DockerComponentRequest):
    field_set_type = PythonRequirementsFile

@rule
async def get_requirement_file_component(req: PythonRequirementsFileRequest,
                                         setup: PythonSetup)->DockerComponent:
    sources = None
    copy_command = []
    if setup.requirement_constraints:
        sources = await Get(Digest, PathGlobs([setup.requirement_constraints]))
        copy_command.append("COPY application/{} .\n".format(setup.requirement_constraints))
    return DockerComponent(
        commands=tuple([*copy_command,
                        "RUN python -m venv --upgrade /.virtual_env\n",
                        "ENV PATH=/.virtual_env/bin:$PATH\n",
                        "ENV VIRTUAL_ENV=/.virtual_env\n",
                        "RUN python -m pip install --upgrade pip\n"]),
        sources=sources
    )

@dataclass(frozen=True)
class PythonRequirements(FieldSet):
    required_fields = (PythonRequirementsField,)
    requirement: PythonRequirementsField


class PythonRequirementsRequest(DockerComponentRequest):
    field_set_type = PythonRequirements


@rule
async def get_requirements(req: PythonRequirementsRequest,
                           setup: PythonSetup,
                           repos: PythonRepos) -> DockerComponent:
    if repos.repos:
        links_args = " ".join("--find-links {}"
                              .format(repo for repo in repos.repos))
    else:
        links_args = ""
    num_indices = len(repos.indexes)
    if num_indices >= 1:
        index_args = f"--index-url {repos.indexes[0]} "
    if num_indices > 1:
        index_args = index_args + " ".join([f"--extra-index-url {url}"
                                            for url in repos.indexes[1:]])
    if num_indices == 0:
        index_args = " --no-index "
    constraint_arg = ""
    if setup.requirement_constraints:
        constraint_arg = f"--constraint {setup.requirement_constraints}"

    commands = tuple("RUN python -m pip install {} {} {} {}\n"
                     .format(index_args,
                             links_args,
                             constraint_arg,
                             lib) for lib in req.fs.requirement.value)
    return DockerComponent(
        commands=commands,
        sources=None,
    )


def rules():
    return [UnionRule(DockerComponentRequest, PythonRequirementsRequest),
            UnionRule(DockerComponentRequest, PythonRequirementsFileRequest),
            *collect_rules()]
