"""CSV loader and role lookup for system-test accounts (``role,email,password,verified,description``)."""
import csv
from pathlib import Path

from climanuvem.common import config
from climanuvem.common.test_account import TestAccount

ROLE_LOGIN_USER = "login_user"
ROLE_PROFILE_USER = "profile_user"
ROLE_UNKNOWN_USER = "unknown_user"


class TestAccounts:
    __test__ = False  # not a pytest test class

    def __init__(self, accounts: list[TestAccount]) -> None:
        self._accounts = accounts

    @classmethod
    def load(cls, path: Path = config.ACCOUNTS_FILE) -> "TestAccounts":
        """Reads the accounts CSV; raises ``FileNotFoundError`` when it does not exist."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Accounts file not found: {path}. Create it from tests/resources/accounts.template.csv "
                "or set ACCOUNTS_FILE."
            )
        with path.open(newline="", encoding="utf-8") as handle:
            return cls([
                TestAccount(
                    role=row["role"].strip(),
                    email=row["email"].strip(),
                    password=row["password"],
                    verified=row["verified"].strip().lower() == "true",
                    description=row["description"].strip(),
                )
                for row in csv.DictReader(handle)
            ])

    def by_role(self, role: str) -> list[TestAccount]:
        return [account for account in self._accounts if account.role == role]

    def _required(self, role: str) -> list[TestAccount]:
        matches = self.by_role(role)
        if not matches:
            raise LookupError(f"Configure at least one account with role '{role}' in ACCOUNTS_FILE.")
        return matches

    def login_accounts(self) -> list[TestAccount]:
        return self._required(ROLE_LOGIN_USER)

    def profile_accounts(self) -> list[TestAccount]:
        return self._required(ROLE_PROFILE_USER)

    def login_account(self) -> TestAccount:
        return self._required(ROLE_LOGIN_USER)[0]

    def profile_account(self) -> TestAccount:
        return self._required(ROLE_PROFILE_USER)[0]

    def unknown_account(self) -> TestAccount:
        return self._required(ROLE_UNKNOWN_USER)[0]
