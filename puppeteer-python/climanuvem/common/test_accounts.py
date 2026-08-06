# -*- coding: utf-8 -*-
"""CSV loader and role lookup for system-test accounts. Mirrors
selenium-java's ``TestAccounts``: loads ``role,email,password,verified,
description`` rows from a CSV file and groups them by role."""
import csv
import logging
from pathlib import Path
from typing import List

from climanuvem.common.test_account import TestAccount

logger = logging.getLogger(__name__)

ROLE_LOGIN_USER = "login_user"
ROLE_PROFILE_USER = "profile_user"
ROLE_UNKNOWN_USER = "unknown_user"


class TestAccounts:
    def __init__(self, accounts: List[TestAccount]):
        self._accounts = accounts

    @classmethod
    def load(cls, accounts_file: str) -> "TestAccounts":
        path = Path(accounts_file)
        if not path.exists():
            logger.warning(
                "Accounts file not found: %s. Create it from tests/resources/accounts.template.csv or set "
                "ACCOUNTS_FILE. Tests that require accounts will fail only when they request one.",
                accounts_file,
            )
            return cls.empty()

        accounts = []
        with open(path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                accounts.append(
                    TestAccount(
                        role=row["role"].strip(),
                        email=row["email"].strip(),
                        password=row["password"],
                        verified=row["verified"].strip().lower() == "true",
                        description=row["description"].strip(),
                    )
                )
        return cls(accounts)

    @classmethod
    def empty(cls) -> "TestAccounts":
        return cls([])

    def by_role(self, role: str) -> List[TestAccount]:
        return [account for account in self._accounts if account.role == role]

    def required_single(self, role: str) -> TestAccount:
        matches = self.by_role(role)
        if not matches:
            raise AssertionError(f"Configure at least one account with role '{role}' in ACCOUNTS_FILE.")
        return matches[0]

    def required(self, role: str) -> List[TestAccount]:
        matches = self.by_role(role)
        if not matches:
            raise AssertionError(f"Configure at least one {role} in ACCOUNTS_FILE.")
        return matches

    def login_accounts(self) -> List[TestAccount]:
        return self.required(ROLE_LOGIN_USER)

    def profile_accounts(self) -> List[TestAccount]:
        return self.required(ROLE_PROFILE_USER)

    def login_account(self) -> TestAccount:
        return self.required_single(ROLE_LOGIN_USER)

    def profile_account(self) -> TestAccount:
        return self.required_single(ROLE_PROFILE_USER)

    def unknown_account(self) -> TestAccount:
        return self.required_single(ROLE_UNKNOWN_USER)
