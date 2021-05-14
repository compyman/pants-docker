import itertools
import logging
from dataclasses import dataclass
from io import StringIO
from typing import List, Tuple

import pants.core.goals.package
from pants.python.python_setup import PythonSetup
from pants.backend.python.target_types import (PythonRequirementsFileSources,
                                               PythonRequirementLibrary,
                                               PythonRequirementsField,
                                               PythonRequirementsFile,
                                               PythonSources)
from pants.core.goals.package import (BuiltPackage, BuiltPackageArtifact,
                                      OutputPathField)
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.core.util_rules.stripped_source_files import StrippedSourceFiles
from pants.engine.addresses import Addresses
from pants.engine.fs import (AddPrefix, CreateDigest, Digest, FileContent,
                             MergeDigests, Snapshot, PathGlobs)
from pants.engine.process import (BinaryPathRequest, BinaryPaths, Process,
                                  ProcessResult)
from pants.engine.rules import Get, MultiGet, collect_rules, rule
from pants.engine.target import (COMMON_TARGET_FIELDS, Dependencies,
                                 DependenciesRequest, HydratedSources,
                                 HydrateSourcesRequest, Sources, StringField,
                                 StringSequenceField, Tags, Target, Targets,
                                 TransitiveTargets, TransitiveTargetsRequest)
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel

from .fields import Docker, DockerPackageFieldSet

logger = logging.getLogger(__name__)


@rule(level=LogLevel.DEBUG)
async def package_into_image(
        python_setup_system: PythonSetup,
    targets: Targets, field_set: DockerPackageFieldSet
) -> BuiltPackage:
    direct_deps = await Get(Targets, DependenciesRequest(field_set.dependencies))
    all_deps = await Get(
        TransitiveTargets, TransitiveTargetsRequest([d.address for d in direct_deps])
    )
    constraints_file = python_setup_system.requirement_constraints
    if constraints_file is not None:
        constraints_get = Get(
            Digest, PathGlobs([constraints_file])
        )
    else:
        constraints_file = "dummy.txt"
        constraints_get = Get(Digest, CreateDigest([FileContent(constraints_file, b"")]))
    sources = [t[Sources] for t in all_deps.closure if t.has_field(Sources)]
    stripped_snapshot = await Get(StrippedSourceFiles, SourceFilesRequest(sources))
    digest = stripped_snapshot.snapshot.digest
    snapshot, constraints_digest = await MultiGet(Get(Snapshot, AddPrefix(digest, "application")),
                                                  constraints_get)

    dockerfile = StringIO()
    dockerfile.write("FROM {}\n".format(field_set.base_image.value))
    if field_set.workdir:
        dockerfile.write("WORKDIR {}\n".format(field_set.workdir.value))
    if field_set.image_setup.value:
        dockerfile.writelines(
            ["RUN {}\n".format(line) for line in field_set.image_setup.value]
        )
    dockerfile.write("COPY {} .\n".format(constraints_file))
    for dep in all_deps.closure:
        if not dep.has_field(PythonRequirementsField):
            continue
        for lib in dep[PythonRequirementsField].value:
            dockerfile.write("RUN pip install {} -c {}\n".format(lib, constraints_file))
    dockerfile.write("RUN rm {}\n".format(constraints_file))
    
    dockerfile.write("COPY application .\n")
    if field_set.command.value:
        cmd_string = "CMD [{}]\n".format(
            ",".join(f'"{cmd}"' for cmd in field_set.command.value)
        )
        dockerfile.write(cmd_string)

    logger.info("DockerFile: \n%s", dockerfile.getvalue())

    dockerfile = await Get(
        Digest,
        CreateDigest(
            [FileContent("Dockerfile", dockerfile.getvalue().encode("utf-8"))]
        ),
    )

    docker_context = await Get(Digest, MergeDigests([dockerfile, snapshot.digest, constraints_digest]))
    docker_context_snapshot = await Get(Snapshot, Digest, docker_context)
    logger.info("Docker Context: \n%s", "\n".join(docker_context_snapshot.files))
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
    tag_arguments = _tag_argument_list(field_set)

    await Get(
        ProcessResult,
        Process(
            argv=[process_path.first_path.path, "build", *tag_arguments, "."],
            input_digest=docker_context,
            description=f"Creating Docker Image from {field_set.image_name.value} and dependencies",
        ),
    )
    artifact = "{}.tar".format(field_set.image_name.value)
    process_result = await Get(
        ProcessResult,
        Process(
            argv=[process_path.first_path.path, "save", "-o", artifact, field_set.image_name.value],
            output_files=[artifact],
            description="Saving Docker Image into tar",
        ),
    )
    o = await Get(Snapshot, Digest, process_result.output_digest)
    return BuiltPackage(
        digest=process_result.output_digest,
        artifacts=([BuiltPackageArtifact(f, ()) for f in o.files]),
    )


def _build_tags(field_set: DockerPackageFieldSet) -> List[str]:
    tags = [f"{field_set.image_name.value}:{tag}" for tag in field_set.tags.value]
    tags.append(field_set.image_name.value)
    if not field_set.registry.value:
        return tags
    registry = field_set.registry.value
    return [f"{registry}/{tag}" for tag in tags]


def _tag_argument_list(field_set: DockerPackageFieldSet) -> List[str]:
    """Turns a list of docker registry/name:tags strings the a list with one
    "-t" before each "registry/name:tag i.e. ["test-container:version-1"] ->

    ["-t", "test-container:version"] which can be used as process
    arguments.
    """
    tags = _build_tags(field_set)
    tags = itertools.chain(*(("-t", tag) for tag in tags))
    return tags


def rules():
    return [
        *collect_rules(),
        UnionRule(pants.core.goals.package.PackageFieldSet, DockerPackageFieldSet),
    ]
