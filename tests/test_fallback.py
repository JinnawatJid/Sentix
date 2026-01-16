import unittest
from unittest.mock import MagicMock, patch
import logging
from src.core.llm import call_llm

# Disable logging during tests
logging.disable(logging.CRITICAL)

class TestLLMFallback(unittest.TestCase):
    @patch('src.core.llm.genai.Client')
    @patch('src.core.llm.os.getenv')
    @patch('src.core.llm.time.sleep') # Skip sleep delay
    def test_fallback_logic(self, mock_sleep, mock_getenv, mock_client_cls):
        # Setup Environment
        mock_getenv.return_value = "fake_key"

        # Setup Mock Client and Models
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance

        # Configure generate_content to raise 429 for the first 4 calls,
        # then succeed on the 5th (which should be the fallback model)

        # Define side effects for generate_content
        # We need to inspect which model was called to verify fallback

        call_count = 0

        def side_effect(model, contents):
            nonlocal call_count
            call_count += 1

            # Attempts 1-4 (Indices 0-3 in loop)
            if call_count <= 4:
                if model == 'gemini-3-flash-preview':
                    raise Exception("429 RESOURCE_EXHAUSTED")
                else:
                    # Should not happen: calling fallback too early or wrong model
                    return MagicMock(text=f"Unexpected model {model}")

            # Attempt 5 (Index 4)
            if call_count == 5:
                if model == 'gemini-2.5-flash':
                    return MagicMock(text="Success with Fallback")
                else:
                     raise Exception(f"Expected fallback model, got {model}")

            return MagicMock(text="Should not reach here")

        mock_client_instance.models.generate_content.side_effect = side_effect

        # Run Function
        result = call_llm("test prompt", model='gemini-3-flash-preview', fallback_model='gemini-2.5-flash')

        # Assertions
        self.assertEqual(result, "Success with Fallback")
        self.assertEqual(call_count, 5) # 4 fails + 1 success

    @patch('src.core.llm.genai.Client')
    @patch('src.core.llm.os.getenv')
    @patch('src.core.llm.time.sleep')
    def test_primary_succeeds(self, mock_sleep, mock_getenv, mock_client_cls):
        mock_getenv.return_value = "fake_key"
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance

        mock_client_instance.models.generate_content.return_value = MagicMock(text="Primary Success")

        result = call_llm("test prompt")

        self.assertEqual(result, "Primary Success")
        # Should only be called once
        mock_client_instance.models.generate_content.assert_called_once()
        args, kwargs = mock_client_instance.models.generate_content.call_args
        self.assertEqual(kwargs['model'], 'gemini-3-flash-preview')

if __name__ == '__main__':
    unittest.main()
