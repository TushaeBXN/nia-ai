"""
Nia AI — AWS Lambda entry point

Receives requests from API Gateway (HTTP API, payload format 2.0).
Runs the full Nia pipeline (intake → triage → verdict) and returns a
structured JSON response.

Environment variables (set in Lambda console or template.yaml):
  NIA_MODEL_BACKEND   bedrock | claude | none  (default: bedrock)
  NIA_BEDROCK_MODEL   Bedrock model ID         (default: meta.llama3-8b-instruct-v1:0)
  NIA_SHARED_DIR      /tmp/nia-shared          (REQUIRED — /var/task is read-only)
  ANTHROPIC_API_KEY   only needed if NIA_MODEL_BACKEND=claude
  AWS_REGION          injected by Lambda automatically
"""

import json
import os

_CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": os.environ.get("NIA_CORS_ORIGIN", "*"),
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def _build_model():
    """Construct the model client based on NIA_MODEL_BACKEND."""
    from nia.model import BedrockClient, ClaudeClient, ModelUnavailable

    backend = os.environ.get("NIA_MODEL_BACKEND", "bedrock").lower()
    if backend == "none":
        return None
    try:
        if backend == "bedrock":
            return BedrockClient()
        if backend == "claude":
            return ClaudeClient()
        # Fall through to no-model mode rather than crashing
        return None
    except ModelUnavailable:
        return None


def handler(event, context):
    http_method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")

    if path == "/health" or path.endswith("/health"):
        return {
            "statusCode": 200,
            "headers": _CORS_HEADERS,
            "body": json.dumps({"status": "ok", "service": "nia-ai"}),
        }

    # OPTIONS preflight for CORS
    if http_method == "OPTIONS":
        return {"statusCode": 204, "headers": _CORS_HEADERS, "body": ""}

    # Parse body — API Gateway may send it as a string or already decoded dict
    raw_body = event.get("body") or "{}"
    if isinstance(raw_body, str):
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            return _error(400, "Request body must be JSON.")
    else:
        body = raw_body

    text = (body.get("message") or "").strip()
    if not text:
        return _error(400, "'message' field is required.")

    if len(text) > 4000:
        return _error(400, "Message too long (4000 character limit).")

    # Run pipeline
    from agents.nia.agent import NiaAgent

    model = _build_model()
    agent = NiaAgent(model_client=model)
    try:
        situation, squad_responses, verdict = agent.handle(text)
    except Exception as e:
        return _error(500, f"Something went wrong. Please try again. ({type(e).__name__})")
    finally:
        agent.close()

    return {
        "statusCode": 200,
        "headers": _CORS_HEADERS,
        "body": json.dumps(
            {
                "verdict": verdict,
                "domain": situation.domain.value,
                "urgency": situation.urgency.value,
                "state": situation.state,
                "squad": list(situation.squad_assignment),
                "model_used": type(model).__name__ if model else "deterministic",
            },
            ensure_ascii=False,
        ),
    }


def _error(status: int, message: str) -> dict:
    return {
        "statusCode": status,
        "headers": _CORS_HEADERS,
        "body": json.dumps({"error": message}),
    }
