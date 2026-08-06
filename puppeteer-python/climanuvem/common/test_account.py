# -*- coding: utf-8 -*-
"""Account row used by the system tests. Mirrors selenium-java's
``TestAccount``."""
from dataclasses import dataclass


@dataclass(frozen=True)
class TestAccount:
    role: str
    email: str
    password: str
    verified: bool
    description: str

    def __str__(self) -> str:
        return f"{self.role}:{self.email}"
