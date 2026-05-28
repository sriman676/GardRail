"""
Custom LLM Callback Integration Example with GuardRail

This example shows how developers can bypass GuardRail's built-in LLM providers
and route all security check queries (fingerprinting, scanner, drift detector)
through a custom central LLM function or internal company API client.
"""
import asyncio
from typing import Optional

from agent.guardrail_wrapper import GuardRail
from core.llm_client import GenericLLMClient

# 1. Define a completely custom LLM handler
# Signature: (prompt: str, system_prompt: Optional[str], json_format: bool) -> str
def my_custom_llm_router(prompt: str, system_prompt: Optional[str] = None, json_format: bool = False) -> str:
    """
    Routs all queries through an custom enterprise gateway, local fine-tuned model,
    or internal API wrapper.
    """
    print(f"\n[Custom Router Called] Json required: {json_format}")
    
    # Handlers must return valid strings, which must be JSON-parseable if json_format=True
    if json_format:
        # Mock answers for different security modules
        if "intent" in prompt.lower() or "forbidden" in prompt.lower():
            return '{"action":"summarize","target":"document","scope":"read-only","forbidden_actions":["send_email"]}'
        elif "injection" in prompt.lower() or "ignore" in prompt.lower():
            return '{"is_injection":false,"confidence":0.95,"explanation":"Legitimate document content"}'
        elif "drift" in prompt.lower() or "behavior" in prompt.lower():
            return '{"drift_score":0.05,"drift_type":"ALIGNED","explanation":"Custom check says aligned."}'
        
        return '{}'
    
    return "Action was successfully completed."


async def main():
    print("--- Running GuardRail with a Custom LLM Gateway ---")
    
    # 2. Setup the GenericLLMClient to use the custom callback
    custom_client = GenericLLMClient(
        provider="custom",
        custom_callable=my_custom_llm_router
    )

    # 3. Instantiate GuardRail and hot-plug the custom LLM client into all security modules
    guard = GuardRail(decision_mode="cli")
    
    # Replace default clients in internal security check instances
    from core.intent_fingerprint import IntentFingerprinter
    guard.fingerprinter = IntentFingerprinter()
    guard.fingerprinter.client = custom_client
    
    guard.scanner.client = custom_client
    guard.drift_detector.client = custom_client
    
    # 4. Execute the pipeline
    clean_text = "Acme service agreement. Terms include $10,000 monthly pay."
    result = await guard.run(
        task="Summarize contract payment term",
        input_content=clean_text
    )

    print(f"\nStatus:       {result['status']}")
    print(f"Scan Threat:  {result.get('scan_threat_level')}")
    print(f"Agent Output: {result.get('output')}")


if __name__ == "__main__":
    asyncio.run(main())
