"""Package a 'docker' Target into a docker image.

Uses the information from a `docker` target in order to build a
Dockerfile & build context and then uses those to construct a docker
image.

Each dependent build target is processed to produce DockerComponents
which has both: files, to be included in the docker build context and
'commands' which will be inserted into the Dockerfile. Each Docker
component has an 'order' attribute which controls when it executes
relative to other docker components.

An implicit command is generated to copy all files in the docker
component into the built image Once all files have been merged into a
digest and the Dockerfile generated, we shell out to docker in order
to actually build the image.

The resulting image is then tagged if any tags were configured as part
of the build target definition.

Please see the ./pants help docker for more information on available
docker target fields, and see the documentation for sources.py,
python_requirements.py for specifics on how the DockerComponents are
generated
"""
import itertools
import logging
from io import StringIO
from typing import Iterable, List, Optional

import sendwave.pants_docker.utils as utils
from pants.core.goals.package import BuiltPackage, BuiltPackageArtifact
from pants.engine.environment import Environment, EnvironmentRequest
from pants.engine.fs import (AddPrefix, CreateDigest, Digest, FileContent,
                             MergeDigests, Snapshot)
from pants.engine.process import (BinaryPathRequest, BinaryPaths, Process,
                                  ProcessResult)
from pants.engine.rules import Get, MultiGet, collect_rules, rule
from pants.engine.target import TransitiveTargets, TransitiveTargetsRequest
from pants.engine.unions import UnionMembership
from sendwave.pants_docker.docker_component import (DockerComponent,
                                                    DockerComponentFieldSet)
from sendwave.pants_docker.target import DockerPackageFieldSet

logger = logging.getLogger(__name__)


def _build_tags(
    target_name: str, tags: List[str], registry: Optional[str]
) -> List[str]:
    """Build a list of docker tags.

    Each tag in the passed in list will be formatted as:
    {registry/}target_name:tag in order to tag a docker image
    """
    tags = [f"{target_name}:{tag}" for tag in tags]
    tags.append(target_name)
    if not registry:
        return tags
    return [f"{registry}/{tag}" for tag in tags]


def _build_tag_argument_list(
    target_name: str, tags: List[str], registry: Optional[str]
) -> List[str]:
    """Build a list of docker tags and format them as CLI arguments.

    Takes the name of the build artifact, a list of tags and an
    optional docker registry and formats them as arguments to the
    docker command line program. Adding a "-t" before each formatted
    "registry/name:tag

    i.e. ('test_container, ['version]) -> ["-t", "test-container:version"]

    If the 'tags' list is empty no tags will be produced
    """
    tags = _build_tags(target_name, tags, registry)
    tags = itertools.chain(*(("-t", tag) for tag in tags))
    return list(tags)


def _create_dockerfile(
    base_image: str,
    workdir: Optional[str],
    setup: Iterable[str],
    commands: Iterable[str],
    init_command: Iterable[str],
) -> str:
    """Construct a Dockerfile and write it into a string variable.

    Uses commands explicitly specified in the docker target definition &
    generated from the Target's dependencies
    """
    dockerfile = StringIO()
    dockerfile.write("FROM {}\n".format(base_image))
    if workdir:
        dockerfile.write("WORKDIR {}\n".format(workdir))
    if setup:
        dockerfile.writelines(["RUN {}\n".format(line) for line in setup])
    dockerfile.writelines(commands)
    dockerfile.write("COPY application .\n")
    if init_command:
        cmd = "CMD [{}]\n".format(",".join('"{}"'.format(c) for c in init_command))
        dockerfile.write(cmd)
    return dockerfile.getvalue()


@rule()
async def package_into_image(
    field_set: DockerPackageFieldSet,
    union_membership: UnionMembership,
) -> BuiltPackage:
    """Build a docker image from a 'docker' build target.

    Creates a build context & dockerfile from the build target & its
    dependencies. Then builds & tags that image. (see the module
    docstring for more information)
    """
    target_name = field_set.address.target_name
    transitive_targets = await Get(
        TransitiveTargets, TransitiveTargetsRequest([field_set.address])
    )
    component_list = []
    logger.debug("Building Target %s", target_name)
    for field_set_type in union_membership[DockerComponentFieldSet]:
        for target in transitive_targets.dependencies:
            if field_set_type.is_applicable(target):
                logger.debug(
                    "Dependent Target %s applies to as component %s",
                    target.address,
                    field_set_type.__name__,
                )
                component_list.append(field_set_type.create(target))

    components = await MultiGet(
        Get(DockerComponent, DockerComponentFieldSet, fs) for fs in component_list
    )

    source_digests = []
    run_commands = []
    components = sorted(components, key=lambda c: c.order)
    for component in components:
        if component.sources:
            source_digests.append(component.sources)
        run_commands.extend(component.commands)
    source_digest = await Get(Digest, MergeDigests(source_digests))
    application_snapshot = await Get(Snapshot, AddPrefix(source_digest, "application"))

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Files to be copied into the docker container")
        for file in application_snapshot.files:
            logger.debug("* %s", file)

    dockerfile_contents = _create_dockerfile(
        field_set.base_image.value,
        field_set.workdir.value,
        field_set.image_setup.value,
        run_commands,
        field_set.command.value,
    )
    logger.debug(dockerfile_contents)
    dockerfile = await Get(
        Digest,
        CreateDigest([FileContent("Dockerfile", dockerfile_contents.encode("utf-8"))]),
    )
    # create docker build context of all merged files & fetch docker
    # connection enviornment variables
    # and the location of the docker process
    search_path = ["/bin", "/usr/bin", "/usr/local/bin", "$HOME/"]
    docker_context, docker_env, docker_paths = await MultiGet(
        Get(Digest, MergeDigests([dockerfile, application_snapshot.digest])),
        Get(Environment, EnvironmentRequest(utils.DOCKER_ENV_VARS)),
        Get(
            BinaryPaths,
            BinaryPathRequest(
                binary_name="docker",
                search_path=search_path,
            ),
        ),
    )
    if not docker_paths.first_path:
        raise ValueError("Unable to locate Docker binary on paths: %s", search_path)
    process_path = docker_paths.first_path.path
    # build an list of arguments of the form ["-t",
    # "registry/name:tag"] to pass to the docker executable
    tag_arguments = _build_tag_argument_list(
        target_name, field_set.tags.value or [], field_set.registry.value
    )
    # create the image
    process_args = [process_path, "build"]
    if not logger.isEnabledFor(logging.DEBUG):
        process_args.append("-q")  # only output the hash of the image
    process_args.extend(tag_arguments)
    process_args.append(".")  # use current (sealed) directory as build context
    process_result = await Get(
        ProcessResult,
        Process(
            env=docker_env,
            argv=process_args,
            input_digest=docker_context,
            description=f"Creating Docker Image from {target_name}",
        ),
    )
    logger.info(process_result.stdout.decode())
    o = await Get(Snapshot, Digest, process_result.output_digest)
    return BuiltPackage(
        digest=process_result.output_digest,
        artifacts=([BuiltPackageArtifact(f, ()) for f in o.files]),
    )


def rules():
    """Return the pants rules for this module."""
    return [
        *collect_rules(),
    ]
