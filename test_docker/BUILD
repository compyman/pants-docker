python_library()

docker(
        name="dockerize",
        image_setup_commands = ["apt-get update && apt-get upgrade --yes", "apt-get -y install gcc libpq-dev"],
        base_image="python:3.8.8-slim-buster",
        image_name="test-docker-application",
        tags=["version1", "version2"],
        command=['python', 'app.py'],
        workdir='root',
        dependencies=["test_docker", "//:gunicorn", "//:gevent",],
)