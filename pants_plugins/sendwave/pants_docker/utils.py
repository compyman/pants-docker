"""Plugin-wide utility functions/data."""

from pants.engine.rules import Get
from pants.engine.environment import Environment, EnvironmentRequest
from pants.engine.process import (BinaryPathRequest, BinaryPaths)
# Docker uses all of these env variables to connect to the docker
# server process
DOCKER_ENV_VARS = [
    "DOCKER_CERT_PATH",
    "DOCKER_CONFIG",
    "DOCKER_CONTENT_TRUST_SERVER",
    "DOCKER_CONTENT_TRUST",
    "DOCKER_CONTEXT",
    "DOCKER_DEFAULT_PLATFORM",
    "DOCKER_HIDE_LEGACY_COMMANDS",
    "DOCKER_HOST",
    "DOCKER_STACK_ORCHESTRATOR",
    "DOCKER_TLS_VERIFY",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
]


def docker_environment() -> Get:
    """Return an awaitable that fetches the current docker environment."""
    return Get(Environment, EnvironmentRequest(DOCKER_ENV_VARS)),


async def docker_executable() -> str:
    """Lookup the docker executable."""
    # Find the docker executable
    search_paths = ["/bin", "/usr/bin", "/usr/local/bin", "$HOME/bin"]
    process_paths = await Get(
        BinaryPaths,
        BinaryPathRequest(
            binary_name="docker",
            search_path=search_paths,
        ),
    )
    if not process_paths.first_path:
        raise ValueError(
            "Unable to locate Docker binary on paths: %s",
            search_paths)
    return process_paths.first_path.path
