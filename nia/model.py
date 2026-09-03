"""
Model clients — local Ollama (default, privacy-first) and Claude API (optional).

Stdlib only, matching chat_nia.py. Every client exposes one method:

    complete(prompt: str, system: str | None = None) -> str

If no model is reachable, callers should catch ModelUnavailable and fall back
to Nia's deterministic (no-model) pathways — the mission system must still
help people when there is no GPU, no API key, and no internet.
"""

import json
import os
import urllib.error
import urllib.request

from . import config


class ModelUnavailable(Exception):
    """Raised when the selected model backend cannot be reached."""


class OllamaClient:
    """Local model via Ollama. Nothing leaves the machine."""

    is_local = True

    def __init__(self, model: str = None, url: str = None):
        self.model = model or config.OLLAMA_MODEL
        self.url = (url or config.OLLAMA_URL).rstrip("/") + "/api/chat"

    def complete(self, prompt: str, system: str = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": False,
        }).encode()

        req = urllib.request.Request(
            self.url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode())
        except (urllib.error.URLError, OSError) as e:
            raise ModelUnavailable(
                f"Cannot reach Ollama at {self.url} — is `ollama serve` running? ({e})"
            )
        return data.get("message", {}).get("content", "")


class ClaudeClient:
    """
    Claude API client (stdlib, no SDK dependency).

    PRIVACY NOTE: this sends the user's situation to a cloud API.
    Never used for immigration interactions — nia.privacy enforces local-only
    handling for maximum-privacy domains.
    """

    is_local = False

    def __init__(self, model: str = None):
        self.model = model or config.ANTHROPIC_MODEL
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ModelUnavailable(
                "ANTHROPIC_API_KEY is not set. Use the local model instead: "
                "python -m nia.cli"
            )

    def complete(self, prompt: str, system: str = None) -> str:
        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        req = urllib.request.Request(
            config.ANTHROPIC_API_URL,
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode())
        except (urllib.error.URLError, OSError) as e:
            raise ModelUnavailable(f"Cannot reach the Claude API ({e})")
        parts = data.get("content", [])
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")


class BedrockClient:
    """
    Amazon Bedrock via the Converse API (model-agnostic).

    boto3 is pre-installed in the Lambda Python runtime — no pip install needed
    in production. For local testing: pip install boto3.

    Default model: Llama 3 8B Instruct (fast, cheap, solid for triage).
    Switch to meta.llama3-70b-instruct-v1:0 or amazon.nova-pro-v1:0 for harder
    reasoning tasks by setting NIA_BEDROCK_MODEL in the Lambda environment.

    PRIVACY NOTE: Bedrock is a cloud call. Immigration interactions refuse
    this client (nia.privacy.policy_for returns allow_cloud=False) and fall
    back to Nia's deterministic, no-model pathways.
    """

    is_local = False

    def __init__(self, model_id: str = None, region: str = None):
        try:
            import boto3
        except ImportError:
            raise ModelUnavailable(
                "boto3 is required for Bedrock — pip install boto3 "
                "(pre-installed in Lambda runtime)"
            )
        self.model_id = (
            model_id
            or os.environ.get("NIA_BEDROCK_MODEL", "meta.llama3-8b-instruct-v1:0")
        )
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=region or os.environ.get("AWS_REGION", "us-east-1"),
        )

    def complete(self, prompt: str, system: str = None) -> str:
        kwargs = {
            "modelId": self.model_id,
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": 2048, "temperature": 0.7},
        }
        if system:
            kwargs["system"] = [{"text": system}]
        try:
            response = self._client.converse(**kwargs)
        except Exception as e:
            raise ModelUnavailable(
                f"Bedrock unreachable or model not enabled ({self.model_id}): {e}"
            )
        return response["output"]["message"]["content"][0]["text"]


def get_client(name: str = "ollama"):
    """
    Build a model client by name.

    Names:
      'bedrock'  — Amazon Bedrock (Lambda default, pay-per-token)
      'claude'   — Anthropic Claude API (requires ANTHROPIC_API_KEY)
      'ollama'   — Local Ollama (local dev default, privacy-first)
      anything else treated as an Ollama model name
    """
    if name == "bedrock":
        return BedrockClient()
    if name == "claude":
        return ClaudeClient()
    return OllamaClient(model=name if name not in ("ollama", None) else None)
