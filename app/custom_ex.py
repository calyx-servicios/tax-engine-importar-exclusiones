"""Custom Exception class for the application"""


class CustomException(Exception):
    """Base class for other exceptions"""

    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors

    def __str__(self):
        return f"{self.message} -> {self.errors}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.message!r})"

    @property
    def message(self):
        """Returns the first argument used to construct this error."""
        return self.message

    @property
    def errors(self):
        """Returns the second argument used to construct this error."""
        return self.errors