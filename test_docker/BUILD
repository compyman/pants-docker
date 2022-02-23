resources(name="resources", sources=["static/*"])

files(name="files", sources=["static/*"])

relocated_files(
    name="relocated",
    files_targets=[":files"],
    # stripping source roots happens after the files are moved
    src="test_docker/static/",
    dest="test_docker/imgs/",
)

python_sources(
    name="test_docker",
    dependencies=[
        ":files",
        ":resources",
        ":relocated",
    ],
)


docker(
    name="dockerized_flask_app",
    image_setup_commands=[
        "apt-get update && apt-get upgrade --yes",
        "apt-get -y install gcc libpq-dev",
    ],
    base_image="python:3.8.8-slim-buster",
    tags=["version1", "version2"],
    # command=["/.virtual_env/bin/python",  "-m", "gunicorn", "test_docker.app:app"],
    command=[
        "/.virtual_env/bin/gunicorn",
        "--bind=127.0.0.1:8000",
        "test_docker.app:app",
    ],
    workdir="root",
    dependencies=[
        "test_docker",
        "//:gunicorn",
        "//:gevent",
    ],
)
