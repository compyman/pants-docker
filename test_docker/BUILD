resources(name="templates",
          sources=["templates/*"])
files(name="static",
          sources=["static/*"])

python_library(
    name="test_docker",
    dependencies=["test_docker:templates",
                  "test_docker:static",]
)

docker(
        name="dockerized_flask_app",
        image_setup_commands = ["apt-get update && apt-get upgrade --yes",
                                "apt-get -y install gcc libpq-dev"],
        base_image="python:3.8.8-slim-buster",
        tags=["version1", "version2"],
        #command=["/.virtual_env/bin/python",  "-m", "gunicorn", "test_docker.app:app"],
        command=["/.virtual_env/bin/gunicorn", "--bind=0.0.0.0:5050", "test_docker.app:app"],
        workdir="root",
        dependencies=["test_docker", "//:gunicorn", "//:gevent",],
)
