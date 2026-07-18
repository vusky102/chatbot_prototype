import sys
import unittest
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage
from openai import RateLimitError

sys.path.append(".")
from main import get_assistant_reply, invoke_llm


class TestTenacity(unittest.TestCase):
    def test_retry_on_rate_limit_error(self):
        llm = MagicMock()
        dummy_response = MagicMock()
        dummy_response.status_code = 429
        dummy_response.headers = {}

        errors = [
            RateLimitError("Rate limit exceeded", response=dummy_response, body=None),
            RateLimitError("Rate limit exceeded", response=dummy_response, body=None),
            AIMessage(content="Success"),
        ]
        llm.invoke.side_effect = errors

        res = invoke_llm(llm, [HumanMessage(content="hello")])

        self.assertEqual(res.content, "Success")
        self.assertEqual(llm.invoke.call_count, 3)

    def test_fallback_called_after_max_retries(self):
        primary = MagicMock()
        primary_bound = MagicMock()
        primary.bind_tools.return_value = primary_bound

        fallback = MagicMock()
        fallback_bound = MagicMock()
        fallback.bind_tools.return_value = fallback_bound

        dummy_response = MagicMock()
        dummy_response.status_code = 429
        dummy_response.headers = {}

        primary_bound.invoke.side_effect = RateLimitError(
            "Rate limit",
            response=dummy_response,
            body=None,
        )
        fallback_bound.invoke.return_value = AIMessage(content="Fallback Success")

        reply = get_assistant_reply(
            llm=primary,
            messages=[HumanMessage(content="hello")],
            fallback_llm=fallback,
        )

        self.assertEqual(reply, "Fallback Success")
        self.assertEqual(primary_bound.invoke.call_count, 3)
        self.assertEqual(fallback_bound.invoke.call_count, 1)


if __name__ == "__main__":
    unittest.main()
