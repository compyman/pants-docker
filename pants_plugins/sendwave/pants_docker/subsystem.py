"""Defines a subsystem which allows setting tags via the command line
or configuration file
"""
from pants.engine.rules import collect_rules
from pants.option.subsystem import Subsystem


class DockerPackageSubsystem(Subsystem):
    options_scope = 'docker-package'
    help = ('Configuration for the python-docker plugin '
            'to set the tags of the resulting image')

    @classmethod
    def register_options(cls, register):
        """Register the 'tags' argument."""
        super().register_options(register)
        register(
            '--tags',
            type=list,
            member_type=str,
            help="List of tags to identify the generated image",
        )
        register(
            '--registry',
            type=str,
            default=None,
            help='docker registry to add to image tags',
        )


def rules():
    return collect_rules()
