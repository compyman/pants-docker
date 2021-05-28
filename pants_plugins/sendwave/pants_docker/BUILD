python_library(
    name="pants-docker",
    dependencies=["pants_plugins:pants",],
)


python_distribution(
    dependencies=[":pants-docker",],
    provides=setup_py(
        name="sendwave-pants-docker",
        version="beta",
        description="Pants Plugin to automatically generate docker images from pants targets",
        author="compyman@compyman.net",
    ),
    setup_py_commands=["sdist", "bdist_wheel"],
)