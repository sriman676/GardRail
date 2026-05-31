import json
import logging
import httpx
from typing import Optional, Callable, Dict, Any

from config import settings

logger = logging.getLogger("guardrail.llm")


class GenericLLMClient:
    """
    A unified, provider-agnostic LLM interface for GuardRail.
    Supports OpenAI, Gemini, Anthropic, Ollama, and Custom callables.
    Features:
    - Auto-detection of official SDKs with seamless httpx REST API fallback.
    - AI-Powered JSON Self-Repair Loop.
    - Provider Failover Routing with detailed diagnostics.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        custom_callable: Optional[Callable[[str, Optional[str], bool], str]] = None,
    ):
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_MODEL
        self.custom_callable = custom_callable

        # Diagnostic log of failures
        self.diagnostics: Dict[str, str] = {}

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_format: bool = False,
        temperature: float = 0.0,
        max_tokens: int = 500,
        fallback_default: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Main entrypoint to generate text or parsed JSON from the LLM.
        Automatically handles provider selection, failover routing, and JSON self-repair.
        """
        self.diagnostics.clear()
        
        # 1. Attempt main provider
        result_str = self._try_provider_chain(
            provider=self.provider,
            model=self.model,
            prompt=prompt,
            system_prompt=system_prompt,
            json_format=json_format,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # 2. If main provider failed, perform failover routing
        if result_str is None:
            result_str = self._execute_failover(
                prompt=prompt,
                system_prompt=system_prompt,
                json_format=json_format,
                temperature=temperature,
                max_tokens=max_tokens
            )

        # 3. If all LLMs failed, fallback to local offline defaults
        if result_str is None:
            logger.error(
                "CRITICAL: All LLM providers failed or are unconfigured! "
                "Attempted: %s. Diagnostics: %s. Falling back to local offline rules.",
                list(self.diagnostics.keys()),
                self.diagnostics
            )
            # Display detailed diagnostics to stdout/stderr so developers know why it failed
            print("\n[GuardRail Security Warning] Offline Fallback Triggered!")
            for prov, err in self.diagnostics.items():
                print(f"  - Provider '{prov}' failed: {err}")
            print("Using local pattern scan and safe defaults.\n")

            if json_format:
                return fallback_default or {}
            return "Fallback response."

        # 4. Handle JSON formatting and self-repair if needed
        if json_format:
            return self._parse_and_repair_json(
                raw_text=result_str,
                temperature=temperature,
                max_tokens=max_tokens,
                fallback_default=fallback_default
            )

        return result_str

    def _try_provider_chain(
        self,
        provider: str,
        model: Optional[str],
        prompt: str,
        system_prompt: Optional[str],
        json_format: bool,
        temperature: float,
        max_tokens: int
    ) -> Optional[str]:
        """Runs a specific provider and catches all exceptions, storing them in diagnostics."""
        provider = provider.lower()
        try:
            if provider == "custom":
                if not self.custom_callable:
                    raise ValueError("LLM_PROVIDER is set to 'custom' but no custom_callable was provided.")
                return self.custom_callable(prompt, system_prompt, json_format)

            elif provider == "openai":
                return self._call_openai(model, prompt, system_prompt, json_format, temperature, max_tokens)

            elif provider == "gemini":
                return self._call_gemini(model, prompt, system_prompt, json_format, temperature, max_tokens)

            elif provider == "anthropic":
                return self._call_anthropic(model, prompt, system_prompt, json_format, temperature, max_tokens)

            elif provider == "nvidia":
                return self._call_nvidia(model, prompt, system_prompt, json_format, temperature, max_tokens)

            elif provider == "ollama":
                return self._call_ollama(model, prompt, system_prompt, json_format, temperature, max_tokens)

            else:
                raise ValueError(f"Unknown LLM provider: {provider}")

        except Exception as e:
            err_msg = f"{type(e).__name__}: {str(e)}"
            logger.warning("Provider '%s' failed. Reason: %s", provider, err_msg)
            self.diagnostics[provider] = err_msg
            return None

    def _execute_failover(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_format: bool,
        temperature: float,
        max_tokens: int
    ) -> Optional[str]:
        """Iterates through all alternative providers that have credentials set."""
        # Define candidate providers in order of preference
        candidates = ["nvidia", "openai", "gemini", "anthropic", "ollama"]
        
        # Exclude the provider we already tried and failed
        candidates = [c for c in candidates if c != self.provider.lower()]

        for candidate in candidates:
            # Check if key/URL is configured before attempting
            if candidate == "nvidia" and not settings.NVIDIA_API_KEY:
                continue
            if candidate == "openai" and not settings.OPENAI_API_KEY:
                continue
            if candidate == "gemini" and not settings.GEMINI_API_KEY:
                continue
            if candidate == "anthropic" and not settings.ANTHROPIC_API_KEY:
                continue

            logger.info("Attempting failover to provider: %s", candidate)
            result = self._try_provider_chain(
                provider=candidate,
                model=None,  # Use intelligent defaults for failovers
                prompt=prompt,
                system_prompt=system_prompt,
                json_format=json_format,
                temperature=temperature,
                max_tokens=max_tokens
            )
            if result is not None:
                logger.info("Failover to '%s' succeeded!", candidate)
                return result

        return None

    # --- OpenAI Provider Implementation ---
    def _call_openai(
        self,
        model: Optional[str],
        prompt: str,
        system_prompt: Optional[str],
        json_format: bool,
        temperature: float,
        max_tokens: int
    ) -> str:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")

        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY, http_client=httpx.Client())
        
        selected_model = model or settings.OPENAI_MODEL or "gpt-4o"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        extra_args = {}
        if json_format:
            extra_args["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(
            model=selected_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30.0,
            **extra_args
        )
        return response.choices[0].message.content

    # --- Google Gemini Provider Implementation ---
    def _call_gemini(
        self,
        model: Optional[str],
        prompt: str,
        system_prompt: Optional[str],
        json_format: bool,
        temperature: float,
        max_tokens: int
    ) -> str:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        selected_model = model or "gemini-2.5-flash"

        # Attempt to use official google-genai or google-generativeai SDK if installed
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            if json_format:
                config.response_mime_type = "application/json"
            if system_prompt:
                config.system_instruction = system_prompt

            response = client.models.generate_content(
                model=selected_model,
                contents=prompt,
                config=config,
            )
            return response.text
        except ImportError:
            # Fall back to google-generativeai older SDK
            try:
                import google.generativeai as google_genai
                google_genai.configure(api_key=api_key)
                generation_config = {"temperature": temperature, "max_output_tokens": max_tokens}
                if json_format:
                    generation_config["response_mime_type"] = "application/json"
                
                model_inst = google_genai.GenerativeModel(
                    model_name=selected_model,
                    generation_config=generation_config,
                    system_instruction=system_prompt
                )
                response = model_inst.generate_content(prompt)
                return response.text
            except ImportError:
                # Direct HTTP REST fallback using httpx
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={api_key}"
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"[System Instruction]\n{system_prompt}\n\n[User Instruction]\n{prompt}"

                body = {
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens,
                    }
                }
                if json_format:
                    body["generationConfig"]["responseMimeType"] = "application/json"

                resp = httpx.post(url, json=body, timeout=30.0)
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

    # --- Anthropic Claude Provider Implementation ---
    def _call_anthropic(
        self,
        model: Optional[str],
        prompt: str,
        system_prompt: Optional[str],
        json_format: bool,
        temperature: float,
        max_tokens: int
    ) -> str:
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set.")

        selected_model = model or "claude-3-5-sonnet-latest"

        # Attempt to use official anthropic SDK
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            
            kwargs = {}
            if system_prompt:
                kwargs["system"] = system_prompt
            
            # Anthropic enforces JSON format via system guidance or prompt injection
            adjusted_prompt = prompt
            if json_format and "json" not in prompt.lower():
                adjusted_prompt = prompt + "\n\nRespond strictly with a valid JSON object."

            response = client.messages.create(
                model=selected_model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": adjusted_prompt}],
                **kwargs
            )
            return response.content[0].text
        except ImportError:
            # Direct HTTP REST fallback using httpx
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            adjusted_prompt = prompt
            if json_format and "json" not in prompt.lower():
                adjusted_prompt = prompt + "\n\nRespond strictly with a valid JSON object."

            body = {
                "model": selected_model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": adjusted_prompt}]
            }
            if system_prompt:
                body["system"] = system_prompt

            resp = httpx.post(url, headers=headers, json=body, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    # --- NVIDIA Provider Implementation ---
    def _call_nvidia(
        self,
        model: Optional[str],
        prompt: str,
        system_prompt: Optional[str],
        json_format: bool,
        temperature: float,
        max_tokens: int
    ) -> str:
        api_key = settings.NVIDIA_API_KEY
        if not api_key:
            raise ValueError("NVIDIA_API_KEY is not set.")

        selected_model = model or settings.NVIDIA_MODEL or "nvidia/llama-2-70b-chat"

        # NVIDIA API is OpenAI-compatible, so use OpenAI SDK with custom base URL
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url="https://integrate.api.nvidia.com/v1",
                http_client=httpx.Client()
            )
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            extra_args = {}
            if json_format:
                extra_args["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=30.0,
                **extra_args
            )
            return response.choices[0].message.content
        except ImportError:
            # Direct HTTP REST fallback using httpx
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            body = {
                "model": selected_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            if json_format:
                body["response_format"] = {"type": "json_object"}

            resp = httpx.post(url, headers=headers, json=body, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # --- Ollama Local Provider Implementation ---
    def _call_ollama(
        self,
        model: Optional[str],
        prompt: str,
        system_prompt: Optional[str],
        json_format: bool,
        temperature: float,
        max_tokens: int
    ) -> str:
        selected_model = model or "llama3"
        url = f"{settings.OLLAMA_BASE_URL}/api/chat"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": selected_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if json_format:
            body["format"] = "json"

        resp = httpx.post(url, json=body, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]

    # --- JSON Helper & Self-Repair ---
    def _parse_and_repair_json(
        self,
        raw_text: str,
        temperature: float,
        max_tokens: int,
        fallback_default: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Cleans response text, parses JSON, and performs self-repair if needed."""
        cleaned_text = raw_text.strip()
        
        # Strip markdown json block wrappers if returned
        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as err:
            logger.warning(
                "JSON parse crash! Failed to decode raw LLM response. Error: %s. "
                "Initiating AI-Powered JSON Self-Repair Loop...",
                str(err)
            )

            # Repair Prompt
            repair_prompt = (
                "You are an expert JSON repair assistant.\n"
                "The following text was generated by a system but failed to parse as valid JSON. "
                "Analyze the malformed input, identify syntactic or formatting errors (e.g. missing commas, unescaped quotes, trailing text, mismatched brackets), and correct them.\n"
                "Return ONLY a clean, valid, parseable JSON object with no markdown block wrappers (no backticks) and no surrounding dialogue or chat filler.\n\n"
                f"Malformed input:\n{cleaned_text}\n"
            )

            try:
                # Try calling the current provider with the repair prompt
                repaired_str = self._try_provider_chain(
                    provider=self.provider,
                    model=self.model,
                    prompt=repair_prompt,
                    system_prompt="You only output valid parseable JSON. Do not write introductory words or code block formatting.",
                    json_format=False,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                if repaired_str is None:
                    # Fallback to alternate providers for repair if primary failed
                    repaired_str = self._execute_failover(
                        prompt=repair_prompt,
                        system_prompt="You only output valid parseable JSON. No backticks.",
                        json_format=False,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )

                if repaired_str:
                    cleaned_repaired = repaired_str.strip()
                    if cleaned_repaired.startswith("```"):
                        lines = cleaned_repaired.splitlines()
                        if lines[0].startswith("```json") or lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        cleaned_repaired = "\n".join(lines).strip()
                    
                    parsed_json = json.loads(cleaned_repaired)
                    logger.info("AI-powered JSON Self-Repair completed successfully!")
                    return parsed_json
            except Exception as repair_err:
                logger.error("JSON Self-Repair attempt failed: %s", str(repair_err))

            # Return fallback default if all parsing and repairs fail
            return fallback_default or {}
