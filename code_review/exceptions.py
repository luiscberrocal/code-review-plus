class CodeReviewError(Exception):
    """A custom exception class for handling errors in the code review process.
    This provides more specific and user-friendly error messages.
    """

    pass


class SimpleGitToolError(CodeReviewError):
    """A custom exception class for handling errors in the simple git tool.
    This provides more specific and user-friendly error messages.
    """

    pass


class ConfigurationError(CodeReviewError):
    """A custom exception class for handling configuration-related errors.
    This provides more specific and user-friendly error messages.
    """

    pass
