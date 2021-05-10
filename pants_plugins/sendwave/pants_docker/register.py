import sendwave.pants_docker.dockerize


def rules():
    return sendwave.pants_docker.dockerize.rules()


def target_types():
    return [sendwave.pants_docker.dockerize.Docker]
