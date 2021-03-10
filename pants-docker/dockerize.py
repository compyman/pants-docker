import logging
from dataclasses import dataclass

from pants.core.goals.package import (
    BuiltPackage,
    BuiltPackageArtifact,
    OutputPathField,
    PackageFieldSet,
)
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.addresses import Addresses
from pants.engine.process import BinaryPathRequest, BinaryPaths, Process, ProcessResult
from pants.engine.rules import Get, rule
from pants.engine.target import TransitiveTargets
from pants.util.logging import LogLevel

from .fields import DockerImageFieldSet
from .targets import DockerTarget

logger = logging.getLogger(__name__)


@rule(level=LogLevel.DEBUG)
async def package_bash_binary(field_set: DockerImageFieldSet) -> BuiltPckage:
    transitive_targets = await Get(TransitiveTargets, Addresses([field_set.address]))
    logger.info("Transitive Targets: %s",
        '\n'.join([tgt for tgt in transitive_targets.closure])
    )
    # sources = await Get(
    #     SourceFiles,
    #     SourceFilesRequest(
    #         tgt[Sources]
    #         for tgt in transitive_targets.closure
    #         if tgt.has_field()
    #     ),
    # )

    # output_filename = field_set.output_path.value_or_default(
    #     field_set.address, file_ending="zip"
    # )
    # result = await Get(
    #     ProcessResult,
    #     Process(
    #         argv=(
    #             zip_program_paths.first_path,
    #             output_filename,
    #             *sources.snapshot.files,
    #         ),
    #         input_digest=sources.snapshot.digest,
    #         description=f"Zip {field_set.address} and its dependencies.",
    #         output_files=(output_filename,),
    #     ),
    # )
    # return BuiltPackage(
    #     result.output_digest, artifacts=(BuiltPackageArtifact(output_filename),)
    # )
    return None
