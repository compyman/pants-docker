import sendwave.pants_docker.package as package
import sendwave.pants_docker.python_requirement as python_requirement
import sendwave.pants_docker.sources as sources
import sendwave.pants_docker.target as target
import sendwave.pants_docker.subsystem as subsystem


def rules():
    return [
        *package.rules(),
        *sources.rules(),
        *python_requirement.rules(),
        *target.rules(),
        *subsystem.rules(),
    ]


def target_types():
    return [target.Docker]
