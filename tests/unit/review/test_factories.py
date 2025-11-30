import re
from datetime import datetime
from pathlib import Path

import pytest

from code_review.plugins.docker.schemas import DockerfileSchema
from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import BranchSchema
from tests.unit.review.factories import (
    BranchSchemaFactory,
    CodeReviewSchemaFactory,
    DockerfileSchemaFactory,
)


class TestBranchSchemaFactory:
    """Test suite for BranchSchemaFactory."""

    def test_create_default_branch(self):
        """Test creating a branch with default values."""
        branch = BranchSchemaFactory()

        assert isinstance(branch, BranchSchema)
        assert isinstance(branch.name, str)
        assert isinstance(branch.author, str)
        assert isinstance(branch.email, str)
        assert "@" in branch.email
        assert isinstance(branch.hash, str)
        assert len(branch.hash) == 40  # SHA1 hash length
        assert isinstance(branch.date, datetime)
        assert branch.linting_errors == -1
        assert branch.min_coverage == 80.0
        assert branch.version is None
        assert branch.changelog_versions == []
        assert branch.requirements_to_update == []
        assert branch.formatting_errors == -1
        assert branch.requirements == []

    def test_create_master_branch(self):
        """Test creating a master branch using Params."""
        branch = BranchSchemaFactory(master=True)

        assert branch.name == "master"
        assert isinstance(branch.author, str)
        assert isinstance(branch.email, str)

    def test_create_main_branch(self):
        """Test creating a main branch using Params."""
        branch = BranchSchemaFactory(main=True)

        assert branch.name == "main"

    def test_create_develop_branch(self):
        """Test creating a develop branch using Params."""
        branch = BranchSchemaFactory(develop=True)

        assert branch.name == "develop"

    def test_create_feature_branch(self):
        """Test creating a feature branch using Params."""
        branch = BranchSchemaFactory(feature=True)

        assert branch.name.startswith("feature/")
        assert len(branch.name.split("/")) == 2

    def test_create_release_branch(self):
        """Test creating a release branch using Params."""
        branch = BranchSchemaFactory(release=True)

        assert branch.name.startswith("release/")
        version_part = branch.name.split("/")[1]
        # Should match pattern like 1.2.3
        assert re.match(r"\d+\.\d+\.\d+", version_part)

    def test_create_hotfix_branch(self):
        """Test creating a hotfix branch using Params."""
        branch = BranchSchemaFactory(hotfix=True)

        assert branch.name.startswith("hotfix/")
        version_part = branch.name.split("/")[1]
        # Should match pattern like 1.2.3
        assert re.match(r"\d+\.\d+\.\d+", version_part)

    def test_multiple_branches_have_different_hashes(self):
        """Test that multiple branches have unique hashes."""
        branch1 = BranchSchemaFactory()
        branch2 = BranchSchemaFactory()

        assert branch1.hash != branch2.hash

    def test_override_factory_attributes(self):
        """Test overriding factory attributes."""
        custom_author = "John Doe"
        custom_email = "john@example.com"

        branch = BranchSchemaFactory(
            author=custom_author,
            email=custom_email,
            linting_errors=5,
            min_coverage=90.0,
        )

        assert branch.author == custom_author
        assert branch.email == custom_email
        assert branch.linting_errors == 5
        assert branch.min_coverage == 90.0


class TestDockerfileSchemaFactory:
    """Test suite for DockerfileSchemaFactory."""

    def test_create_default_dockerfile(self):
        """Test creating a dockerfile with default values."""
        dockerfile = DockerfileSchemaFactory()

        assert isinstance(dockerfile, DockerfileSchema)
        assert dockerfile.version == "1.0"
        assert dockerfile.expected_version is None
        assert dockerfile.product == "python"
        assert isinstance(dockerfile.file, Path)
        assert dockerfile.image is None
        assert dockerfile.expected_image is None

    def test_override_dockerfile_attributes(self):
        """Test overriding dockerfile factory attributes."""
        custom_path = Path("/custom/Dockerfile")
        custom_version = "3.11"

        dockerfile = DockerfileSchemaFactory(
            version=custom_version,
            product="node",
            file=custom_path,
        )

        assert dockerfile.version == custom_version
        assert dockerfile.product == "node"
        assert dockerfile.file == custom_path

    def test_multiple_dockerfiles_have_same_defaults(self):
        """Test that multiple dockerfiles share default values."""
        dockerfile1 = DockerfileSchemaFactory()
        dockerfile2 = DockerfileSchemaFactory()

        assert dockerfile1.product == dockerfile2.product
        assert dockerfile1.version == dockerfile2.version


class TestCodeReviewSchemaFactory:
    """Test suite for CodeReviewSchemaFactory."""

    def test_create_default_code_review(self):
        """Test creating a code review with default values."""
        review = CodeReviewSchemaFactory()

        assert isinstance(review, CodeReviewSchema)
        assert isinstance(review.name, str)
        assert review.is_rebased is False
        assert isinstance(review.source_folder, Path)
        assert isinstance(review.makefile_path, Path)
        assert isinstance(review.readme_file, Path)
        assert isinstance(review.ci_file, Path)
        assert isinstance(review.date_created, datetime)
        assert isinstance(review.ticket, str)
        assert isinstance(review.target_branch, BranchSchema)
        assert isinstance(review.base_branch, BranchSchema)
        assert isinstance(review.source_branch_name, str)
        assert isinstance(review.docker_files, list)
        assert isinstance(review.rules_validated, list)

    def test_base_branch_defaults_to_master(self):
        """Test that base_branch defaults to master."""
        review = CodeReviewSchemaFactory()

        assert review.base_branch.name == "master"

    def test_target_branch_defaults_to_feature(self):
        """Test that target_branch defaults to feature branch."""
        review = CodeReviewSchemaFactory()

        assert review.target_branch.name.startswith("feature/")

    def test_ticket_format(self):
        """Test that ticket follows the expected pattern."""
        review = CodeReviewSchemaFactory()

        # Should match pattern like VPOP-1234, PM-334, MON-569
        assert re.match(r"[A-Z]{2,4}-\d{1,4}", review.ticket)

    def test_multiple_reviews_have_different_tickets(self):
        """Test that multiple reviews have unique tickets."""
        review1 = CodeReviewSchemaFactory()
        review2 = CodeReviewSchemaFactory()

        # High probability they will be different
        assert review1.ticket != review2.ticket or review1.name != review2.name

    def test_override_branches(self):
        """Test overriding branch configurations."""
        review = CodeReviewSchemaFactory(
            base_branch=BranchSchemaFactory(develop=True),
            target_branch=BranchSchemaFactory(release=True),
        )

        assert review.base_branch.name == "develop"
        assert review.target_branch.name.startswith("release/")

    def test_override_code_review_attributes(self):
        """Test overriding code review factory attributes."""
        custom_name = "my-project"
        custom_ticket = "CUSTOM-999"

        review = CodeReviewSchemaFactory(
            name=custom_name,
            ticket=custom_ticket,
            is_rebased=True,
        )

        assert review.name == custom_name
        assert review.ticket == custom_ticket
        assert review.is_rebased is True

    def test_docker_files_is_list(self):
        """Test that docker_files is a list."""
        review = CodeReviewSchemaFactory()

        assert isinstance(review.docker_files, list)
        assert len(review.docker_files) == 1
        assert isinstance(review.docker_files[0], DockerfileSchema)

    def test_rules_validated_is_empty_list(self):
        """Test that rules_validated defaults to empty list."""
        review = CodeReviewSchemaFactory()

        assert isinstance(review.rules_validated, list)
        assert len(review.rules_validated) == 0

    def test_create_review_with_custom_docker_files(self):
        """Test creating review with custom docker files."""
        dockerfile1 = DockerfileSchemaFactory(product="python")
        dockerfile2 = DockerfileSchemaFactory(product="node")

        review = CodeReviewSchemaFactory(
            docker_files=[dockerfile1, dockerfile2]
        )

        assert len(review.docker_files) == 2
        assert review.docker_files[0].product == "python"
        assert review.docker_files[1].product == "node"

    def test_create_review_for_hotfix(self):
        """Test creating a review for a hotfix scenario."""
        review = CodeReviewSchemaFactory(
            base_branch=BranchSchemaFactory(main=True),
            target_branch=BranchSchemaFactory(hotfix=True),
        )

        assert review.base_branch.name == "main"
        assert review.target_branch.name.startswith("hotfix/")

    def test_pydantic_validation_works(self):
        """Test that Pydantic validation works on factory output."""
        review = CodeReviewSchemaFactory()

        # Should be able to convert to dict and back
        review_dict = review.model_dump()
        assert isinstance(review_dict, dict)
        assert "name" in review_dict
        assert "ticket" in review_dict
        assert "target_branch" in review_dict

    def test_multiple_reviews_are_independent(self):
        """Test that multiple reviews don't share mutable state."""
        review1 = CodeReviewSchemaFactory()
        review2 = CodeReviewSchemaFactory()

        # Modify one review's list
        review1.rules_validated.append("test_rule")

        # Should not affect the other review
        assert len(review2.rules_validated) == 0

