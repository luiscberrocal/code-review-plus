"""Tests for Django model handlers and visitors."""
from pathlib import Path

import pytest

from code_review.plugins.django.models_handlers import (
    check_model_inheritance,
    lint_django_models,
)


class TestDjangoModelInheritanceVisitor:
    """Tests for DjangoModelInheritanceVisitor class."""

    @pytest.fixture
    def temp_model_file(self, tmp_path):
        """Create a temporary model file for testing."""
        def _create_file(content):
            model_file = tmp_path / "models.py"
            model_file.write_text(content)
            return model_file
        return _create_file

    def test_model_with_both_required_bases(self, temp_model_file):
        """Test that a model with both required base classes passes validation."""
        content = """
class AuditableModel:
    pass

class TimeStampedModel:
    pass

class MyModel(AuditableModel, TimeStampedModel):
    name = models.CharField(max_length=100)
"""
        model_file = temp_model_file(content)
        errors = check_model_inheritance(model_file)
        assert len(errors) == 0

    def test_model_missing_one_required_base(self, temp_model_file):
        """Test that a model missing one required base class fails validation."""
        content = """
class TimeStampedModel:
    pass

class MyModel(TimeStampedModel):
    name = models.CharField(max_length=100)
"""
        model_file = temp_model_file(content)
        errors = check_model_inheritance(model_file)
        assert len(errors) == 1
        assert "MyModel" in errors[0]
        assert "AuditableModel" in errors[0]

    def test_model_missing_both_required_bases(self, temp_model_file):
        """Test that a model missing both required base classes fails validation."""
        content = """
class SomeOtherBase:
    pass

class MyModel(SomeOtherBase):
    name = models.CharField(max_length=100)
"""
        model_file = temp_model_file(content)
        errors = check_model_inheritance(model_file)
        assert len(errors) == 1
        assert "MyModel" in errors[0]
        assert "AuditableModel" in errors[0]
        assert "TimeStampedModel" in errors[0]

    def test_multiple_models_with_mixed_inheritance(self, temp_model_file):
        """Test multiple models with different inheritance patterns."""
        content = """
class AuditableModel:
    pass

class TimeStampedModel:
    pass

class GoodModel(AuditableModel, TimeStampedModel):
    name = models.CharField(max_length=100)

class BadModel(TimeStampedModel):
    name = models.CharField(max_length=100)

class AnotherBadModel(AuditableModel):
    name = models.CharField(max_length=100)
"""
        model_file = temp_model_file(content)
        errors = check_model_inheritance(model_file)
        assert len(errors) == 2
        assert any("BadModel" in error and "AuditableModel" in error for error in errors)
        assert any("AnotherBadModel" in error and "TimeStampedModel" in error for error in errors)

    def test_model_with_django_models_module_inheritance(self, temp_model_file):
        """Test that models inheriting from models.Model are detected."""
        content = """
import django.db.models as models

class MyModel(models.Model):
    name = models.CharField(max_length=100)
"""
        model_file = temp_model_file(content)
        errors = check_model_inheritance(model_file)
        assert len(errors) == 1
        assert "MyModel" in errors[0]

    def test_custom_required_bases(self, temp_model_file):
        """Test with custom required base classes."""
        content = """
class CustomBase:
    pass

class MyModel(CustomBase):
    name = models.CharField(max_length=100)
"""
        model_file = temp_model_file(content)
        errors = check_model_inheritance(model_file, required_bases=["CustomBase", "AnotherBase"])
        assert len(errors) == 1
        assert "MyModel" in errors[0]
        assert "AnotherBase" in errors[0]
        assert "CustomBase" not in errors[0]  # CustomBase is present

    def test_non_model_classes_are_ignored(self, temp_model_file):
        """Test that non-Django model classes are ignored."""
        content = """
class RegularClass:
    def __init__(self):
        self.name = "test"

class AnotherRegularClass:
    value = 42
"""
        model_file = temp_model_file(content)
        errors = check_model_inheritance(model_file)
        assert len(errors) == 0

    def test_empty_file(self, temp_model_file):
        """Test with an empty file."""
        content = ""
        model_file = temp_model_file(content)
        errors = check_model_inheritance(model_file)
        assert len(errors) == 0

    def test_fixture_payment_order_model(self):
        """Test with the actual fixture file - PaymentOrder should pass."""
        fixture_file = Path(__file__).parent.parent.parent.parent / "fixtures/django/models.py"
        if not fixture_file.exists():
            pytest.skip("Fixture file not found")

        errors = check_model_inheritance(fixture_file)
        # PaymentOrder has both AuditableModel and TimeStampedModel
        # ReconciliationPayment only has TimeStampedModel
        assert len(errors) == 1
        assert "ReconciliationPayment" in errors[0]
        assert "AuditableModel" in errors[0]

    def test_reversed_order_of_base_classes(self, temp_model_file):
        """Test that order of base classes doesn't matter."""
        content = """
class AuditableModel:
    pass

class TimeStampedModel:
    pass

class MyModel(TimeStampedModel, AuditableModel):
    name = models.CharField(max_length=100)
"""
        model_file = temp_model_file(content)
        errors = check_model_inheritance(model_file)
        assert len(errors) == 0

    def test_model_with_additional_bases(self, temp_model_file):
        """Test model with more base classes than required."""
        content = """
class AuditableModel:
    pass

class TimeStampedModel:
    pass

class ExtraBase:
    pass

class MyModel(AuditableModel, TimeStampedModel, ExtraBase):
    name = models.CharField(max_length=100)
"""
        model_file = temp_model_file(content)
        errors = check_model_inheritance(model_file)
        assert len(errors) == 0


class TestDjangoModelLinting:
    """Tests for Django model field linting."""

    @pytest.fixture
    def temp_model_file(self, tmp_path):
        """Create a temporary model file for testing."""
        def _create_file(content):
            model_file = tmp_path / "models.py"
            model_file.write_text(content)
            return model_file
        return _create_file

    def test_db_index_warning(self, temp_model_file):
        """Test that db_index=True generates a warning."""
        content = """
class BaseModel:
    pass

class MyModel(BaseModel):
    name = models.CharField(max_length=100, db_index=True, help_text="Name field")
"""
        model_file = temp_model_file(content)
        errors = lint_django_models(model_file)
        assert any("db_index" in error for error in errors)
        assert any("indexes" in error for error in errors)

    def test_missing_help_text_warning(self, temp_model_file):
        """Test that missing help_text generates a warning."""
        content = """
class BaseModel:
    pass

class MyModel(BaseModel):
    name = models.CharField(max_length=100)
"""
        model_file = temp_model_file(content)
        errors = lint_django_models(model_file)
        assert any("help_text" in error and "Missing" in error for error in errors)

    def test_non_translatable_help_text_warning(self, temp_model_file):
        """Test that non-translatable help_text generates a warning."""
        content = """
class BaseModel:
    pass

class MyModel(BaseModel):
    name = models.CharField(max_length=100, help_text="This is not translatable")
"""
        model_file = temp_model_file(content)
        errors = lint_django_models(model_file)
        assert any("help_text" in error and "gettext_lazy" in error for error in errors)

    def test_field_with_all_best_practices(self, temp_model_file):
        """Test that a well-configured field produces no warnings (except help_text translation)."""
        content = """
class BaseModel:
    pass

class MyModel(BaseModel):
    name = models.CharField(max_length=100, help_text=_("Name field"))
"""
        model_file = temp_model_file(content)
        errors = lint_django_models(model_file)
        # Should have no errors about missing help_text or db_index
        assert not any("Missing" in error and "help_text" in error for error in errors)
        assert not any("db_index" in error for error in errors)

    def test_fixture_file_linting(self):
        """Test linting with the actual fixture file."""
        fixture_file = Path(__file__).parent.parent.parent.parent / "fixtures/django/models.py"
        if not fixture_file.exists():
            pytest.skip("Fixture file not found")

        errors = lint_django_models(fixture_file)
        # We know PaymentOrder.status is missing help_text
        assert any("status" in error and "help_text" in error for error in errors)
        # We know several fields have db_index=True
        assert any("db_index" in error for error in errors)


class TestVisitorIntegration:
    """Integration tests for both visitors working together."""

    def test_comprehensive_model_validation(self, tmp_path):
        """Test both inheritance and field linting together."""
        content = """
class AuditableModel:
    pass

class TimeStampedModel:
    pass

class GoodModel(AuditableModel, TimeStampedModel):
    name = models.CharField(max_length=100, help_text=_("Name"))
    
class BadInheritance(TimeStampedModel):
    title = models.CharField(max_length=100, db_index=True)
"""
        model_file = tmp_path / "models.py"
        model_file.write_text(content)

        # Check inheritance
        inheritance_errors = check_model_inheritance(model_file)
        assert len(inheritance_errors) == 1
        assert "BadInheritance" in inheritance_errors[0]

        # Check field linting
        linting_errors = lint_django_models(model_file)
        assert len(linting_errors) > 0
        assert any("db_index" in error for error in linting_errors)

