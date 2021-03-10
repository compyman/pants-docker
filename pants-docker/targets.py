from pants.engine.target import Dependencies, Sources, Target, Tags

class DockerTarget(Target):
    alias = "docker"
    core_fields = (Sources, Dependencies, Tags)

