python_library(
    name="pants_docker_library",
    dependencies=["pants_plugins:pants",],
)


python_distribution(
    name="pants_docker",
    dependencies=[":pants_docker_library",],
    provides=setup_py(
        name="sendwave-pants-docker",
        version="0.04",
        description="Pants Plugin to automatically generate docker images from pants targets",
        author="compyman@compyman.net",
    ),
    setup_py_commands=["sdist", "bdist_wheel"],
)

python_tests(
    name="tests",
)
