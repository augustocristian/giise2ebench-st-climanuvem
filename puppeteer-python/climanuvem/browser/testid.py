"""Selector builder for the frontend ``data-testid`` contract (React Native ``testID`` props)."""


class TestId:
    __test__ = False  # not a pytest test class despite the name

    @staticmethod
    def of(test_id: str) -> str:
        """CSS selector for a test id, e.g. ``TestId.of("login-submit-button")``."""
        return f"[data-testid='{test_id}']"
