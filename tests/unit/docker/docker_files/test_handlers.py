from platform import python_version

from code_review.docker.docker_files.handlers import get_python_version_from_dockerfile


def test_dockerfile_handler(fixtures_folder):
    compose_folder = fixtures_folder / "compose"
    dockerfiles = list(compose_folder.glob("**/Dockerfile"))
    for dockerfile in dockerfiles:
        content = dockerfile.read_text()
        python_version = get_python_version_from_dockerfile(content)
        print("Python version:", python_version)