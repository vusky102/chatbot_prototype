import sys
import unittest
from unittest.mock import MagicMock
from openai import RateLimitError, APIError

# Add workspace root to path
sys.path.append('.')
from main import call_chat_completion, get_assistant_reply, RETRIEVE_KNOWLEDGE_TOOL

class TestTenacity(unittest.TestCase):
    def test_retry_on_rate_limit_error(self):
        # Mock client's completion create method to raise RateLimitError twice and then succeed
        client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Success"
        mock_response.choices[0].message.tool_calls = None
        
        # RateLimitError requires response and body
        dummy_response = MagicMock()
        dummy_response.status_code = 429
        dummy_response.headers = {}
        
        errors = [
            RateLimitError("Rate limit exceeded", response=dummy_response, body=None),
            RateLimitError("Rate limit exceeded", response=dummy_response, body=None),
            mock_response
        ]
        client.chat.completions.create.side_effect = errors
        
        res = call_chat_completion(client, "test-model", [{"role": "user", "content": "hello"}], [RETRIEVE_KNOWLEDGE_TOOL])
        
        self.assertEqual(res.choices[0].message.content, "Success")
        self.assertEqual(client.chat.completions.create.call_count, 3)

    def test_fallback_called_after_max_retries(self):
        # If client always raises RateLimitError, it should raise and get caught by get_assistant_reply which switches to fallback
        client = MagicMock()
        fallback_client = MagicMock()
        
        dummy_response = MagicMock()
        dummy_response.status_code = 429
        dummy_response.headers = {}
        
        # Primary client fails always (which triggers tenacity reraise after 3 attempts)
        client.chat.completions.create.side_effect = RateLimitError("Rate limit", response=dummy_response, body=None)
        
        # Fallback client succeeds
        fallback_response = MagicMock()
        fallback_response.choices = [MagicMock()]
        fallback_response.choices[0].message.content = "Fallback Success"
        fallback_response.choices[0].message.tool_calls = None
        fallback_client.chat.completions.create.return_value = fallback_response
        
        messages = [{"role": "user", "content": "hello"}]
        reply = get_assistant_reply(
            client=client,
            model="primary-model",
            messages=messages,
            fallback_client=fallback_client,
            fallback_model="fallback-model"
        )
        
        self.assertEqual(reply, "Fallback Success")
        self.assertEqual(client.chat.completions.create.call_count, 3)
        self.assertEqual(fallback_client.chat.completions.create.call_count, 1)

if __name__ == "__main__":
    unittest.main()
