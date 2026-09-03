# Nia AI — AWS Serverless Deployment

Lambda + API Gateway + Amazon Bedrock. No servers. Pay per request.

## Prerequisites

```bash
# AWS CLI
brew install awscli
aws configure   # set access key, secret, region (us-east-1 recommended)

# AWS SAM CLI
brew tap aws/tap
brew install aws-sam-cli
```

## Enable Bedrock Models

Before deploying, enable the models in the AWS console:

1. Open **Amazon Bedrock → Model access** in the target region
2. Request access to:
   - `Meta Llama 3 8B Instruct` (default — fast, cheap)
   - `Meta Llama 3 70B Instruct` (optional — higher quality)
3. Access is granted instantly for most models

## Deploy

```bash
cd nia-ai/deploy

# First deploy (creates stack + S3 bucket for artifacts)
sam build --template template.yaml
sam deploy --guided \
  --stack-name nia-ai \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM

# Follow prompts, save samconfig.toml for future deploys
```

After deploy, SAM prints the API URL:
```
NiaApiUrl  https://<id>.execute-api.us-east-1.amazonaws.com/prod/chat
```

## Test

```bash
# Full pipeline test
curl -X POST https://<your-api-url>/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "My landlord is refusing to fix my heat and it is January."}'

# Immigration (triggers max-privacy mode — no model call, deterministic response)
curl -X POST https://<your-api-url>/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "ICE officers came to my door this morning."}'

# Health check
curl https://<your-api-url>/health
```

## Update Deploys

```bash
sam build --template template.yaml && sam deploy
```

## Environment Variables

Set these in the Lambda console or `template.yaml` Globals section:

| Variable | Default | Notes |
|---|---|---|
| `NIA_MODEL_BACKEND` | `bedrock` | `bedrock` \| `claude` \| `none` |
| `NIA_BEDROCK_MODEL` | `meta.llama3-8b-instruct-v1:0` | Any enabled Bedrock model ID |
| `NIA_SHARED_DIR` | *(required)* | Must be `/tmp/nia-shared` in Lambda |
| `NIA_CORS_ORIGIN` | `*` | Lock to your domain in production |
| `ANTHROPIC_API_KEY` | — | Only needed if `NIA_MODEL_BACKEND=claude` |

## Cost Estimate

At 1,000 sessions/month (each ~3K tokens in + 1K out):

| Service | Cost |
|---|---|
| Lambda (512MB, ~10s avg) | ~$0.02 |
| API Gateway HTTP API | ~$0.01 |
| Bedrock Llama 3 8B | ~$0.88 |
| **Total** | **~$1/month** |

Lambda free tier: 1M requests/month — effectively $0 until significant scale.

## Scaling Up

- Switch `NIA_BEDROCK_MODEL` to `meta.llama3-70b-instruct-v1:0` for better reasoning (~10× cost, still cheap)
- Add `ReservedConcurrentExecutions: 10` to the function for predictable scaling
- Add CloudWatch alarms on error rate and p99 latency
- For high-traffic deployments, add DynamoDB with 24h TTL for optional returning-user context

## WhatsApp / SMS (Phase 3)

Wire Twilio to this same Lambda via webhook:
1. Twilio receives SMS/WhatsApp → calls `POST /chat` with `{"message": "<body>"}`
2. Lambda returns verdict
3. Add a Twilio response formatter in `lambda_handler.py` (check `event.get("source") == "twilio"`)
