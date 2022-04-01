python_sources(
    name="pants_docker_library",
    dependencies=[
        "pants_plugins:pants",
    ],
)


python_distribution(
    name="pants_docker",
    dependencies=[
        ":pants_docker_library",
    ],
    provides=setup_py(
        name="sendwave-pants-docker",
        version="1.0",
        description="Pants Plugin to automatically generate docker images from pants targets",
        author="compyman@compyman.net",
    ),
    sdist=True,
    wheel=True,
)

python_tests(
    name="tests",
)
