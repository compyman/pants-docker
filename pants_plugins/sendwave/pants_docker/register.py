"""Register Sendwave pants-docker plugin rules with the pants build system."""
import sendwave.pants_docker.package as package
import sendwave.pants_docker.python_requirement as python_requirement
import sendwave.pants_docker.sources as sources
import sendwave.pants_docker.subsystem as subsystem
import sendwave.pants_docker.target as target


def rules():
    """Collect all pants rules in the plugin."""
    return [
        *subsystem.rules(),
        *package.rules(),
        *sources.rules(),
        *python_requirement.rules(),
        *target.rules(),
    ]


def target_types():
    """Collect the one new target type we've added."""
    return [target.Docker]
