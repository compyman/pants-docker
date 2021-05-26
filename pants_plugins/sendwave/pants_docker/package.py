import itertools
import logging
from dataclasses import dataclass
from io import StringIO
from typing import List, Tuple, Coroutine, Any, Optional

from pants.python.python_setup import PythonSetup
from pants.core.goals.package import (BuiltPackage, BuiltPackageArtifact,
                                      OutputPathField)
from pants.engine.fs import (AddPrefix, CreateDigest, Digest, FileContent,
                             MergeDigests, Snapshot, PathGlobs, )
from pants.engine.process import (BinaryPathRequest, BinaryPaths, Process,
                                  ProcessResult)
from pants.engine.rules import Get, MultiGet, collect_rules, rule
from pants.engine.target import (DependenciesRequest, 
                                 Targets,
                                 TransitiveTargets,
                                 TransitiveTargetsRequest)
import sendwave.pants_docker.docker_component as docker
from pants.engine.unions import UnionMembership
from pants.util.logging import LogLevel

from sendwave.pants_docker.target import Docker, DockerPackageFieldSet
from sendwave.pants_docker.docker_component import DockerComponent, DockerComponentRequest
from sendwave.pants_docker.python_constraints import ConstraintsRequest, ConstraintsDigest

logger = logging.getLogger(__name__)

def build_tags(target_name: str, field_set: DockerPackageFieldSet) -> List[str]:
    tags = [f"{target_name}:{tag}" for tag in field_set.tags.value]
    tags.append(target_name)
    if not field_set.registry.value:
        return tags
    registry = field_set.registry.value
    return [f"{registry}/{tag}" for tag in tags]


def build_tag_argument_list(target_name: str,
                            field_set: DockerPackageFieldSet) -> List[str]:
    """Turns a list of docker registry/name:tags strings the a list with one
    "-t" before each "registry/name:tag i.e. ["test-container:version-1"] ->

    ["-t", "test-container:version"] which can be used as process
    arguments.
    """
    tags = build_tags(target_name, field_set)
    tags = itertools.chain(*(("-t", tag) for tag in tags))
    return tags


@rule(level=LogLevel.DEBUG)
async def package_into_image(
        python_setup_system: PythonSetup,
        field_set: DockerPackageFieldSet,
        um: UnionMembership
) -> BuiltPackage:
    target_name = field_set.address._target_name
    direct_deps = await Get(Targets, DependenciesRequest(field_set.dependencies))
    all_deps = await Get(TransitiveTargets, TransitiveTargetsRequest([d.address for d in direct_deps]))
    dockerization_requests = docker.from_dependencies(all_deps.closure, um)
    components = await MultiGet([Get(DockerComponent,
                                     DockerComponentRequest,
                                     req)
                                 for req in dockerization_requests])
    source_snapshots = []
    run_commands = []
    for component in components:
        if component.sources:
            source_snapshots.append(component.sources.digest)
        run_commands.extend(component.commands)

    digest, constraints = await MultiGet(
        Get(Digest, AddPrefix(await Get(Digest, MergeDigests(digests=source_snapshots)), "application")),
        Get(ConstraintsDigest,
            ConstraintsRequest(python_setup_system.requirement_constraints)),
    )
    dockerfile = StringIO()
    dockerfile.write("FROM {}\n".format(field_set.base_image.value))
    if field_set.workdir:
        dockerfile.write("WORKDIR {}\n".format(field_set.workdir.value))
    if field_set.image_setup.value:
        dockerfile.writelines(
            ["RUN {}\n".format(line) for line in field_set.image_setup.value]
        )
    dockerfile.write("COPY {} .\n".format(constraints.file_name))
    dockerfile.writelines(run_commands)
    dockerfile.write("RUN rm {}\n".format(constraints.file_name))
    dockerfile.write("COPY application .\n")
    if field_set.command.value:
        cmd_string = "CMD [{}]\n".format(
            ",".join(f'"{cmd}"' for cmd in field_set.command.value)
        )
        dockerfile.write(cmd_string)

    logger.debug("DockerFile: \n%s", dockerfile.getvalue())

    dockerfile = await Get(
        Digest,
        CreateDigest(
            [FileContent("Dockerfile", dockerfile.getvalue().encode("utf-8"))]
        ),
    )
    snapshot = await Get(Snapshot, Digest, digest)
    logger.info("Files %s", snapshot.files)
    docker_context = await Get(Digest, MergeDigests([dockerfile,
                                                     snapshot.digest,
                                                     constraints.digest]))
    search_paths = ["/bin", "/usr/bin", "/usr/local/bin", "$HOME/bin"]
    process_path = await Get(
        BinaryPaths,
        BinaryPathRequest(
            binary_name="docker",
            search_path=search_paths,
        ),
    )
    if not process_path.first_path:
        raise ValueError("Unable to locate Docker binary on paths: %s", search_paths)
    tag_arguments =  build_tag_argument_list(target_name, field_set)

    process_result = await Get(
        ProcessResult,
        Process(
            argv=[process_path.first_path.path, "build", *tag_arguments, "."],
            input_digest=docker_context,
            description=f"Creating Docker Image from {target_name} and dependencies",
        ),
    )
    logger.info(process_result.stdout.decode())
    logger.info(process_result.stderr.decode())
    o = await Get(Snapshot, Digest, process_result.output_digest)
    return BuiltPackage(
        digest=process_result.output_digest,
        artifacts=([BuiltPackageArtifact(f, ()) for f in o.files]),
    )


def rules():
    return [
        *collect_rules(),
    ]
