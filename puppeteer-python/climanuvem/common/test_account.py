"""Account row used by the parameterized system tests."""
from dataclasses import dataclass


@dataclass(frozen=True)
class TestAccount:
    __test__ = False  # not a pytest test class

    role: str
    email: str
    password: str
    verified: bool
    description: str

    def __str__(self) -> str:
        return f"{self.role}:{self.email}"
