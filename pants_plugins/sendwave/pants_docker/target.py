from dataclasses import dataclass

import pants.core.goals.package
from pants.core.goals.package import (BuiltPackage, BuiltPackageArtifact,
                                      OutputPathField)
from pants.engine.target import (COMMON_TARGET_FIELDS, Dependencies,
                                 DependenciesRequest, DescriptionField,
                                 HydratedSources, HydrateSourcesRequest,
                                 StringField, StringSequenceField,
                                 Tags, Target, Targets, TransitiveTargets,
                                 TransitiveTargetsRequest)
from pants.engine.unions import UnionRule


class BaseImage(StringField):
    alias = "base_image"
    required = True
    help = "This is used to set the Base Image for all future pants build steps (e.g. python:3.8.8-slim-buster)"


class DockerIgnore(StringSequenceField):
    alias = "docker_ignore"
    required = False
    default = []
    help = "A list of directories to exclude from the docker build context, each entry should be a valid line in a .dockerignore file"


class ImageSetup(StringSequenceField):
    alias = "image_setup_commands"
    required = False
    default = []
    help = 'Commands to run in the image during the build process. Each will be evaluated as it\'s own process in the container and will create a new layer in the resulting image (e.g. ["apt-get update && apt-get upgrade --yes", "apt-get -y install gcc libpq-dev"],)'


class WorkDir(StringField):
    alias = "workdir"
    required = False
    default = "container"
    help = "The directory inside the container into which"


class Registry(StringField):
    alias = "registry"
    required = False
    help = "The registry of the resulting docker image"


class Tags(StringSequenceField):
    alias = "tags"
    default = []
    required = False
    help = 'A list of tags to apply to the resulting docker image (e.g. ["1.0.0", "main"]) '


class Command(StringSequenceField):
    alias = "command"
    default = []
    required = False
    help = "Command used to run the Docker container"


@dataclass(frozen=True)
class DockerPackageFieldSet(pants.core.goals.package.PackageFieldSet):
    alias = "docker_field_set"
    required_fields = (BaseImage,)

    base_image: BaseImage
    image_setup: ImageSetup
    ignore: DockerIgnore
    registry: Registry
    tags: Tags
    dependencies: Dependencies
    workdir: WorkDir
    command: Command
    output_path: OutputPathField


class Docker(Target):
    help = "A docker image that will contain all the source files of its transitive dependencies"
    alias = "docker"
    core_fields = (
        DescriptionField,
        Dependencies,
        BaseImage,
        ImageSetup,
        OutputPathField,
        WorkDir,
        Tags,
        Command,
    )


def rules():
    return [UnionRule(pants.core.goals.package.PackageFieldSet, DockerPackageFieldSet)]
