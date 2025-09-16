from code_review.docker.docker_files.handlers import get_versions_from_dockerfile, parse_dockerfile


def test_dockerfile_handler(fixtures_folder):
    compose_folder = fixtures_folder / "compose"
    dockerfiles = list(compose_folder.glob("**/Dockerfile"))
    for dockerfile in dockerfiles:
        content = dockerfile.read_text()
        version = get_versions_from_dockerfile(content)
        print(dockerfile, " version:", version)


def test_parse_dockerfile(fixtures_folder):
    compose_folder = fixtures_folder / "compose"
    dockerfiles = list(compose_folder.glob("**/Dockerfile"))
    for dockerfile in dockerfiles:
        dockerfile_schema = parse_dockerfile(dockerfile)
        print(dockerfile, " schema:", dockerfile_schema)