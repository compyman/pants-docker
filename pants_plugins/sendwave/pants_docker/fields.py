from dataclasses import dataclass

import pants.core.goals.package
from pants.core.goals.package import (BuiltPackage, BuiltPackageArtifact,
                                      OutputPathField)
from pants.engine.target import (COMMON_TARGET_FIELDS, Dependencies,
                                 DependenciesRequest, DescriptionField,
                                 HydratedSources, HydrateSourcesRequest,
                                 Sources, StringField, StringSequenceField,
                                 Tags, Target, Targets, TransitiveTargets,
                                 TransitiveTargetsRequest)


class DockerField:
    def process(self, set: pants.core.goals.package.PackageFieldSet) -> None:
        pass


class BaseImage(StringField, DockerField):
    alias = "base_image"
    required = True
    help = "This is used to set the Base Image for all future pants build steps (e.g. python:3.8.8-slim-buster)"


class ImageSetup(StringSequenceField, DockerField):
    alias = "image_setup_commands"
    required = False
    default = []
    help = 'Commands to run in the image during the build process. Each will be evaluated as it\'s own process in the container and will create a new layer in the resulting image (e.g. ["apt-get update && apt-get upgrade --yes", "apt-get -y install gcc libpq-dev"],)'


class WorkDir(StringField, DockerField):
    alias = "workdir"
    required = False
    default = "container"
    help = "The directory inside the container into which"


class ImageName(StringField, DockerField):
    alias = "image_name"
    required = True
    help = "The name of the resulting docker image"


class Registry(StringField, DockerField):
    alias = "registry"
    required = False
    help = "The registry of the resulting docker image"


class Tags(StringSequenceField, DockerField):
    alias = "tags"
    default = []
    required = False
    help = 'A list of tags to apply to the resulting docker image (e.g. ["1.0.0", "main"]) '


class Command(StringSequenceField, DockerField):
    alias = "command"
    required = False
    help = "Command used to run the Docker container"


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
        ImageName,
        Tags,
        Command,
    )


@dataclass(frozen=True)
class DockerPackageFieldSet(pants.core.goals.package.PackageFieldSet):
    alias = "docker_field_set"
    required_fields = (BaseImage, ImageName)

    base_image: BaseImage
    image_name: ImageName
    image_setup: ImageSetup
    registry: Registry
    tags: Tags
    dependencies: Dependencies
    workdir: WorkDir
    command: Command
