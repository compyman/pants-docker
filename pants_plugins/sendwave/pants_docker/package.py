import itertools
import logging
from dataclasses import dataclass
from io import StringIO
from typing import List, Tuple, Coroutine, Any, Optional, Iterable
from pants.engine.environment import Environment, EnvironmentRequest
from pants.python.python_setup import PythonSetup
from pants.core.goals.package import (BuiltPackage, BuiltPackageArtifact,
                                      OutputPathField)
from pants.engine.fs import (AddPrefix, CreateDigest, Digest, FileContent,
                             MergeDigests, PathGlobs, Snapshot)
from pants.engine.process import (BinaryPathRequest, BinaryPaths, Process,
                                  ProcessResult)
from pants.engine.rules import Get, MultiGet, collect_rules, rule
from pants.engine.target import (DependenciesRequest, Targets,
                                 TransitiveTargets, TransitiveTargetsRequest)
from pants.engine.unions import UnionMembership
from pants.python.python_setup import PythonSetup
from pants.util.logging import LogLevel
from sendwave.pants_docker.docker_component import (DockerComponent,
                                                    DockerComponentRequest)
from sendwave.pants_docker.target import Docker, DockerPackageFieldSet

logger = logging.getLogger(__name__)

DOCKER_ENV_VARS = ["DOCKER_CERT_PATH",
                   "DOCKER_CONFIG",
                   "DOCKER_CONTENT_TRUST_SERVER",
                   "DOCKER_CONTENT_TRUST",
                   "DOCKER_CONTEXT",
                   "DOCKER_DEFAULT_PLATFORM",
                   "DOCKER_HIDE_LEGACY_COMMANDS",
                   "DOCKER_HOST",
                   "DOCKER_STACK_ORCHESTRATOR",
                   "DOCKER_TLS_VERIFY",
                   "HTTP_PROXY",
                   "HTTPS_PROXY",
                   "NO_PROXY",]

def _build_tags(target_name: str, field_set: DockerPackageFieldSet) -> List[str]:
    tags = [f"{target_name}:{tag}" for tag in field_set.tags.value]
    tags.append(target_name)
    if not field_set.registry.value:
        return tags
    registry = field_set.registry.value
    return [f"{registry}/{tag}" for tag in tags]


def _build_tag_argument_list(
    target_name: str, field_set: DockerPackageFieldSet
) -> List[str]:
    """Turns a list of docker registry/name:tags strings the a list with one
    "-t" before each "registry/name:tag i.e. ["test-container:version-1"] ->

    ["-t", "test-container:version"] which can be used as process
    arguments.
    """
    tags = _build_tags(target_name, field_set)
    tags = itertools.chain(*(("-t", tag) for tag in tags))
    return tags


def _create_dockerfile(
    base_image: str,
    workdir: Optional[str],
    setup: Iterable[str],
    commands: Iterable[str],
    init_command: Iterable[str],
) -> StringIO:
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

    logger.info("DockerFile: \n%s", dockerfile.getvalue())
    return dockerfile


@rule(level=LogLevel.DEBUG)
async def package_into_image(
    python_setup_system: PythonSetup,
    field_set: DockerPackageFieldSet,
    um: UnionMembership,
) -> BuiltPackage:
    target_name = field_set.address._target_name
    direct_deps = await Get(Targets, DependenciesRequest(field_set.dependencies))
    all_deps = await Get(
        TransitiveTargets, TransitiveTargetsRequest([d.address for d in direct_deps])
    )
    dockerization_requests = await docker.from_dependencies(all_deps.closure, um)
    components = await MultiGet(
        [
            Get(DockerComponent, DockerComponentRequest, req)
            for req in dockerization_requests
        ]
    )
    source_digests = []
    run_commands = []
    components = sorted(components, key=lambda c: c.order)
    for component in components:
        if component.sources:
            source_digests.append(component.sources)
        run_commands.extend(component.commands)
    source_digest = await Get(Digest, MergeDigests(digests=source_digests))
    application_digest = await Get(Digest, AddPrefix(source_digest, "application"))
    snapshot = await Get(Snapshot, Digest, application_digest)
    logger.info(snapshot.files)
    dockerfile_contents = _create_dockerfile(
        field_set.base_image.value,
        field_set.workdir and field_set.workdir.value,
        field_set.image_setup.value,
        run_commands,
        field_set.command.value,
    )
    dockerfile = await Get(
        Digest,
        CreateDigest(
            [FileContent("Dockerfile", dockerfile_contents.getvalue().encode("utf-8"))]
        ),
    )
    docker_context = await Get(Digest, MergeDigests([dockerfile, application_digest]))

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

    tag_arguments =  _build_tag_argument_list(target_name, field_set)
    docker_env = await Get(Environment, EnvironmentRequest(DOCKER_ENV_VARS))
>
    process_result = await Get(
        ProcessResult,
        Process(
            env=docker_env,
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
