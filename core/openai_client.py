import httpx
from openai import OpenAI

from config import settings


def create_openai_client() -> OpenAI:
    """Create an OpenAI client compatible with httpx 0.28+.

    openai==1.30.0 constructs an internal httpx client with the removed
    `proxies` kwarg when httpx 0.28 is installed globally. Passing an explicit
    client avoids that constructor path while preserving the pinned OpenAI SDK.
    """
    return OpenAI(api_key=settings.OPENAI_API_KEY, http_client=httpx.Client())
