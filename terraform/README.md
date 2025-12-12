# Infrastructure as Code - Terraform Configuration

This directory contains Terraform configuration for deploying the AI-Chat Orchestrator to Google Cloud Platform.

## Architecture

The infrastructure includes:

- **Cloud Run Services**: Containerized services for Gemini AI
- **Artifact Registry**: Docker image repository
- **Secret Manager**: Secure storage for API keys and tokens
- **Cloud Monitoring**: Custom metrics and dashboards for observability
- **Service Accounts**: IAM configuration for secure access

## Prerequisites

1. **Install Terraform**:
   ```bash
   brew install terraform  # macOS
   # or download from https://www.terraform.io/downloads
   ```

2. **Install gcloud CLI**:
   ```bash
   brew install google-cloud-sdk  # macOS
   # or download from https://cloud.google.com/sdk/docs/install
   ```

3. **Authenticate with GCP**:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

4. **Create GCP Project**:
   ```bash
   # Create a new project (or use existing)
   gcloud projects create YOUR_PROJECT_ID --name="AI Chat Orchestrator"

   # Set as default
   gcloud config set project YOUR_PROJECT_ID

   # Enable billing (required for Cloud Run)
   # Visit: https://console.cloud.google.com/billing/linkedaccount?project=YOUR_PROJECT_ID
   ```

## Setup

1. **Configure Variables**:
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   ```

   Edit `terraform.tfvars` with your GCP project details:
   ```hcl
   project_id  = "your-gcp-project-id"
   region      = "us-central1"
   zone        = "us-central1-a"
   environment = "dev"
   ```

2. **Initialize Terraform**:
   ```bash
   terraform init
   ```

3. **Review Plan**:
   ```bash
   terraform plan
   ```

4. **Apply Configuration**:
   ```bash
   terraform apply
   ```

   Type `yes` when prompted.

## Storing Secrets

After infrastructure is created, add your API keys to Secret Manager:

```bash
# Gemini API Key
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets versions add gemini-api-key --data-file=-

# Discord Client ID
echo -n "YOUR_DISCORD_CLIENT_ID" | gcloud secrets versions add discord-client-id --data-file=-

# Discord Client Secret
echo -n "YOUR_DISCORD_CLIENT_SECRET" | gcloud secrets versions add discord-client-secret --data-file=-

# Slack Bot Token
echo -n "YOUR_SLACK_BOT_TOKEN" | gcloud secrets versions add slack-bot-token --data-file=-
```

## Building and Deploying Docker Images

1. **Authenticate Docker with Artifact Registry**:
   ```bash
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```

2. **Build and Push Gemini Service**:
   ```bash
   # Get the Artifact Registry URL from Terraform output
   export REGISTRY_URL=$(terraform output -raw artifact_registry_url)

   # Build Docker image
   docker build -f Dockerfile.gemini -t ${REGISTRY_URL}/gemini-service:latest .

   # Push to Artifact Registry
   docker push ${REGISTRY_URL}/gemini-service:latest
   ```

3. **Deploy to Cloud Run**:
   ```bash
   # Cloud Run will automatically use the latest image
   # Or manually update:
   gcloud run deploy gemini-ai-service \
     --image ${REGISTRY_URL}/gemini-service:latest \
     --region us-central1
   ```

## Monitoring

Access your telemetry dashboard:

1. Get dashboard URL:
   ```bash
   terraform output dashboard_url
   ```

2. Or visit Cloud Console:
   ```
   https://console.cloud.google.com/monitoring/dashboards
   ```

The dashboard shows:
- **Request Latency**: Average time for API calls
- **Success Rate**: Percentage of successful requests
- **Failure Rate**: Percentage of failed requests

## Testing the Deployment

1. **Get Service URL**:
   ```bash
   export SERVICE_URL=$(terraform output -raw gemini_service_url)
   echo $SERVICE_URL
   ```

2. **Test Health Endpoint**:
   ```bash
   curl ${SERVICE_URL}/health
   ```

3. **Test AI Generation**:
   ```bash
   curl -X POST ${SERVICE_URL}/generate \
     -H "Content-Type: application/json" \
     -d '{
       "user_input": "What is 2+2?",
       "system_prompt": "You are a helpful assistant"
     }'
   ```

## Outputs

After `terraform apply`, you'll see:

- `gemini_service_url`: Public URL of Gemini service
- `artifact_registry_url`: Docker registry URL
- `service_account_email`: Service account for Cloud Run
- `dashboard_url`: Monitoring dashboard URL
- `secrets`: Names of Secret Manager secrets

## Cost Estimates

With GCP Free Tier and $300 credits:

- **Cloud Run**: Free tier includes 2M requests/month
- **Artifact Registry**: 0.5 GB free storage/month
- **Secret Manager**: First 6 secrets free
- **Cloud Monitoring**: Free tier includes custom metrics

Estimated monthly cost for dev environment: **$0-5** (within free tier)

## Cleanup

To destroy all infrastructure:

```bash
terraform destroy
```

**Warning**: This will delete all resources including stored secrets.

## Directory Structure

```
terraform/
├── main.tf                    # Main infrastructure configuration
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── terraform.tfvars.example   # Example variables file
└── README.md                  # This file
```

## Troubleshooting

### Error: API not enabled

If you see errors about APIs not being enabled:

```bash
gcloud services enable compute.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### Error: Billing not enabled

Enable billing in GCP Console:
```
https://console.cloud.google.com/billing/linkedaccount?project=YOUR_PROJECT_ID
```

### Docker build fails

Make sure you're in the project root directory:
```bash
cd /Users/shriranjanpatil/Data/NYU/Fall_25/OSPD/hw1
docker build -f Dockerfile.gemini -t test-image .
```

## CI/CD Integration

To integrate with CircleCI:

1. Add GCP service account key to CircleCI environment
2. Add deployment step to `.circleci/config.yml`
3. Terraform state can be stored in GCS bucket for team access

## Next Steps

1. ✅ Infrastructure setup complete
2. 🔲 Build and push Docker images
3. 🔲 Configure secrets in Secret Manager
4. 🔲 Deploy services to Cloud Run
5. 🔲 Verify monitoring dashboard
6. 🔲 Run integration tests against deployed services
