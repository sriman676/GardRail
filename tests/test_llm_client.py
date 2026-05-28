from unittest.mock import MagicMock, patch

from core.llm_client import GenericLLMClient


def test_custom_callable_succeeds():
    def custom_cb(prompt, sys, json_fmt):
        return "custom result"

    client = GenericLLMClient(provider="custom", custom_callable=custom_cb)
    result = client.generate("test prompt")
    assert result == "custom result"


def test_json_self_repair_loop():
    client = GenericLLMClient(provider="custom")
    
    # Simulate a malformed JSON first, followed by a valid JSON repair response
    calls = []
    def custom_cb(prompt, sys, json_fmt):
        calls.append(prompt)
        if "repair" in prompt.lower():
            return '{"status": "repaired"}'
        return '{"status": "broken", ' # malformed JSON (missing closing braces)

    client.custom_callable = custom_cb
    result = client.generate("get status", json_format=True)
    
    # Verify both the initial check and the repair loop were executed
    assert len(calls) == 2
    assert "repair" in calls[1].lower()
    assert result == {"status": "repaired"}


def test_failover_routing_on_primary_failure():
    # OpenAI fails, but since Gemini key is configured, failover occurs
    client = GenericLLMClient(provider="openai")
    
    with patch("core.llm_client.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "openai-key"
        mock_settings.GEMINI_API_KEY = "gemini-key"
        mock_settings.LLM_PROVIDER = "openai"

        # Mock the individual call methods
        client._call_openai = MagicMock(side_effect=Exception("OpenAI rate limit!"))
        client._call_gemini = MagicMock(return_value="Gemini to the rescue!")

        result = client.generate("hello")
        
        # Verify OpenAI was tried first, failed, and then Gemini succeeded
        client._call_openai.assert_called_once()
        client._call_gemini.assert_called_once()
        assert result == "Gemini to the rescue!"
