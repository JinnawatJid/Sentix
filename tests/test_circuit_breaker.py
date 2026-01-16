import unittest
from unittest.mock import MagicMock, patch
import time
from src.core import llm

class TestCircuitBreaker(unittest.TestCase):
    def setUp(self):
        # Reset global state before each test
        llm._FAILURE_COUNT = 0
        llm._FALLBACK_ACTIVE = False
        llm._FALLBACK_UNTIL = 0

        # Patch environment variable
        self.env_patcher = patch.dict('os.environ', {'GEMINI_API_KEY': 'fake_key'})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch('src.core.llm.genai.Client')
    def test_switch_to_fallback_after_4_failures(self, mock_client_cls):
        """Verify that after 4 consecutive 429s, the system switches to fallback model globally."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Simulate 429 Error
        error_429 = Exception("429 Resource Exhausted")
        mock_client.models.generate_content.side_effect = error_429

        # Speed up sleeps
        with patch('time.sleep', return_value=None):
            # Call 1 (Will fail retries and increment count)
            # Each call_llm tries 5 times.
            # If all 5 fail with 429, it counts as failures.
            # Wait, my logic increments failure count on EACH 429 inside the loop.
            # If max_retries=5, one call_llm could trigger the threshold if it hits 429 four times?
            # Let's check the code:
            # "if not _FALLBACK_ACTIVE ...: _FAILURE_COUNT += 1"
            # Yes, inside the loop. So one single request that retries 4 times will trigger the global breaker.
            # This is actually GOOD because it stops the bleeding faster.

            # Let's verify behavior.
            # Attempt 1: 429 -> Count=1
            # Attempt 2: 429 -> Count=2
            # Attempt 3: 429 -> Count=3
            # Attempt 4: 429 -> Count=4 -> ACTIVE = True

            llm.call_llm("test prompt")

            self.assertTrue(llm._FALLBACK_ACTIVE, "Fallback should be active after repeated failures")
            self.assertEqual(llm._FAILURE_COUNT, 4)

            # Now verify next call uses fallback immediately
            # Reset side effect to success to see which model is called
            mock_client.models.generate_content.side_effect = None
            mock_client.models.generate_content.return_value.text = "Success"

            llm.call_llm("test prompt 2")

            # The args should show the fallback model
            args, _ = mock_client.models.generate_content.call_args
            # call_args could be by name
            kwargs = mock_client.models.generate_content.call_args.kwargs

            # Check used model
            used_model = kwargs.get('model')
            self.assertEqual(used_model, 'gemini-2.5-flash', "Should use fallback model immediately")

    @patch('src.core.llm.genai.Client')
    def test_cooldown_expiry(self, mock_client_cls):
        """Verify that system reverts to primary after cooldown."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.return_value.text = "Success"

        # Manually set state to Active but Expired
        llm._FALLBACK_ACTIVE = True
        llm._FALLBACK_UNTIL = time.time() - 10 # 10 seconds ago

        llm.call_llm("test prompt")

        # Should have reset
        self.assertFalse(llm._FALLBACK_ACTIVE)
        self.assertEqual(llm._FAILURE_COUNT, 0)

        # Should use primary model
        kwargs = mock_client.models.generate_content.call_args.kwargs
        self.assertEqual(kwargs.get('model'), 'gemini-3-flash-preview')

if __name__ == '__main__':
    unittest.main()
