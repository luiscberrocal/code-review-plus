import factory
from faker import Faker
from pathlib import Path
from datetime import datetime
from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import BranchSchema, RulesResult
from code_review.plugins.docker.schemas import DockerfileSchema

fake = Faker()

class BranchSchemaFactory(factory.Factory):
    class Meta:
        model = BranchSchema

    name = factory.LazyAttribute(lambda _: fake.git_branch())
    author = factory.LazyAttribute(lambda _: fake.name())
    email = factory.LazyAttribute(lambda _: fake.email())
    hash = factory.LazyAttribute(lambda _: fake.sha1())
    date = factory.LazyAttribute(lambda _: datetime.now())
    linting_errors = -1
    min_coverage = 80.0
    version = None
    changelog_versions = []
    requirements_to_update = []
    formatting_errors = -1
    requirements = []

class DockerfileSchemaFactory(factory.Factory):
    class Meta:
        model = DockerfileSchema

    version = "1.0"
    expected_version = None
    product = "python"
    file = factory.LazyAttribute(lambda _: Path("/tmp/Dockerfile"))
    image = None
    expected_image = None

class CodeReviewSchemaFactory(factory.Factory):
    class Meta:
        model = CodeReviewSchema

    name = factory.LazyAttribute(lambda _: fake.word())
    is_rebased = False
    source_folder = factory.LazyAttribute(lambda _: Path("/tmp/project"))
    makefile_path = factory.LazyAttribute(lambda _: Path("/tmp/Makefile"))
    readme_file = factory.LazyAttribute(lambda _: Path("/tmp/README.md"))
    ci_file = factory.LazyAttribute(lambda _: Path("/tmp/.gitlab-ci.yml"))
    date_created = factory.LazyAttribute(lambda _: datetime.now())
    ticket = factory.LazyAttribute(lambda _: fake.uuid4())
    target_branch = factory.SubFactory(BranchSchemaFactory)
    base_branch = factory.SubFactory(BranchSchemaFactory)
    source_branch_name = factory.LazyAttribute(lambda _: fake.word())
    docker_files = factory.LazyAttribute(lambda _: [DockerfileSchemaFactory()])
    rules_validated = factory.LazyAttribute(lambda _: [])