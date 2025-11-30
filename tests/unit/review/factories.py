from pyexpat import features

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

    name = factory.LazyAttribute(lambda _: f"branch/{fake.word()}")
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

    class Params:
        # Git flow standard branches
        master = factory.Trait(
            name="master"
        )
        main = factory.Trait(
            name="main"
        )
        develop = factory.Trait(
            name="develop"
        )
        feature = factory.Trait(
            name=factory.LazyAttribute(lambda _: f"feature/{fake.word()}")
        )
        release = factory.Trait(
            name=factory.LazyAttribute(lambda _: f"release/{fake.numerify('%.#.#')}")
        )
        hotfix = factory.Trait(
            name=factory.LazyAttribute(lambda _: f"hotfix/{fake.numerify('%.#.#')}")
        )

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
    ticket = factory.LazyAttribute(lambda _: f"{fake.lexify('????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ').upper()}-{fake.random_int(min=1, max=9999)}")
    target_branch = factory.SubFactory(BranchSchemaFactory, feature=True)
    base_branch = factory.SubFactory(BranchSchemaFactory, master=True)
    source_branch_name = factory.LazyAttribute(lambda _: fake.word())
    docker_files = factory.LazyAttribute(lambda _: [DockerfileSchemaFactory()])
    rules_validated = factory.LazyAttribute(lambda _: [])