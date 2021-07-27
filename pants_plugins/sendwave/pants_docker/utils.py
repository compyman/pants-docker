"""Plugin-wide utility data."""

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
