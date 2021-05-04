import pants_docker.dockerize as dockerize


def rules():
    return dockerize.rules()


def target_types():
    return [dockerize.Docker]
