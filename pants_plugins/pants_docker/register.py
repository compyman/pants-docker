import pants_docker.dockerize as dockerize
from pants_docker.dockerize import Docker


def rules():
    return dockerize.rules()


def target_types():
    return [Docker]
