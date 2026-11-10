"""Input request DTOs for the collaborator application boundary."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

#: Pragmatic email shape check: one "@", no whitespace, and a dot in domain.
_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class CollaboratorCreateDTO(BaseModel):
    """Input contract for registering a collaborator."""

    model_config = ConfigDict(frozen=True)

    name: str
    email: str = Field(pattern=_EMAIL_PATTERN)
    department: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        """
        Trim the email before pattern validation.

        Args:
            value: Proposed collaborator email.

        Returns:
            The trimmed email.

        Raises:
            ValueError: If the email is not a string.
        """
        if not isinstance(value, str):
            raise ValueError("email must be a string")
        return value.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Ensure the collaborator name is present and meaningful.

        Args:
            value: Proposed collaborator name.

        Returns:
            The trimmed name.

        Raises:
            ValueError: If the name is empty or whitespace only.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be empty")
        return stripped

    @field_validator("department")
    @classmethod
    def validate_department(cls, value: str) -> str:
        """
        Ensure the department is present and meaningful.

        Args:
            value: Proposed collaborator department.

        Returns:
            The trimmed department.

        Raises:
            ValueError: If the department is empty or whitespace only.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("department must not be empty")
        return stripped


class EnrollmentCreateDTO(BaseModel):
    """Input contract for enrolling a collaborator in a career path."""

    model_config = ConfigDict(frozen=True)

    path_id: UUID
    target_level: str

    @field_validator("target_level")
    @classmethod
    def validate_target_level(cls, value: str) -> str:
        """
        Ensure the target level is present and meaningful.

        Args:
            value: Proposed target level name.

        Returns:
            The trimmed target level.

        Raises:
            ValueError: If the target level is empty or whitespace only.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("target_level must not be empty")
        return stripped
