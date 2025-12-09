---
name: policyengine-infrastructure
description: PolicyEngine infrastructure deployment patterns using GCP, Terraform, and GitHub Actions
---

# PolicyEngine Infrastructure and Deployment

This skill documents PolicyEngine's infrastructure patterns, focusing on GCP deployment with Terraform and CI/CD automation.

## GCP Project Structure

### Standard Project Naming

PolicyEngine uses descriptive GCP project names:
- **Production APIs**: `policyengine-api-v2`, `policyengine-api-v2-alpha`
- **Pattern**: `policyengine-[service]-[version]-[environment?]`

### Storage Bucket Naming

Cloud Storage buckets follow similar conventions:
- **Pattern**: Match project name or use descriptive suffix
- **Example**: For project `policyengine-api-v2-alpha`, use `policyengine-api-v2-alp` (if full name unavailable)

**Note**: GCP bucket names have restrictions:
- Must be globally unique
- 3-63 characters
- Lowercase letters, numbers, hyphens
- No underscores

## GCP Cloud Run Deployment

### Standard Architecture

PolicyEngine API services typically use:
- **Compute**: Cloud Run (container-based, autoscaling)
- **Storage**: Cloud Storage buckets (for data, artifacts)
- **CI/CD**: GitHub Actions with Workload Identity Federation
- **IAC**: Terraform for infrastructure management

### Why Cloud Run?

Chosen for:
- Persistent URLs (unlike some AWS setups)
- Automatic scaling
- Container-based deployment
- Good integration with GCP services

## Terraform Patterns

### Directory Structure

```
terraform/
├── main.tf              # Primary resource definitions
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── provider.tf          # Provider configuration
├── backend.tf          # Remote state configuration (optional)
└── versions.tf         # Provider version constraints
```

### Standard main.tf Structure

```hcl
# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Cloud Storage bucket
resource "google_storage_bucket" "main" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90  # Adjust as needed
    }
  }
}

# Cloud Run service
resource "google_cloud_run_service" "api" {
  name     = "policyengine-api"
  location = var.region

  template {
    spec {
      containers {
        image = var.container_image

        resources {
          limits = {
            cpu    = "2000m"
            memory = "2Gi"
          }
        }

        env {
          name  = "BUCKET_NAME"
          value = google_storage_bucket.main.name
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# IAM for public access (if needed)
resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
```

### Standard variables.tf

```hcl
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "Cloud Storage bucket name"
  type        = string
}

variable "container_image" {
  description = "Container image to deploy"
  type        = string
  default     = "gcr.io/cloudrun/hello"  # Placeholder
}
```

### Terraform Workflow

```bash
# Initialize
terraform init

# Plan changes
terraform plan

# Apply changes
terraform apply

# View outputs
terraform output
```

## GitHub Actions CI/CD

### Workload Identity Federation

PolicyEngine uses OIDC for secure, keyless authentication to GCP:

**Benefits:**
- No service account keys to manage
- Temporary credentials
- Fine-grained permissions
- Secure by default

### Standard Deployment Workflow

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  id-token: write  # Required for OIDC

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      # Authenticate to GCP using OIDC
      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      # Setup Cloud SDK
      - uses: google-github-actions/setup-gcloud@v2

      # Build and push container
      - name: Build and Push Container
        run: |
          gcloud builds submit \
            --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/api:${{ github.sha }}

      # Deploy to Cloud Run
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy policyengine-api \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/api:${{ github.sha }} \
            --region us-central1 \
            --platform managed \
            --allow-unauthenticated
```

### Required GitHub Secrets

For OIDC authentication:
- `WIF_PROVIDER`: Workload Identity Provider resource name
- `WIF_SERVICE_ACCOUNT`: Service account email
- `GCP_PROJECT_ID`: GCP project ID

**Setup reference**: See existing repos like `policyengine-api-v2` for working examples.

### Testing Before Deploy

```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        pytest tests/
```

## Common Deployment Tasks

### Task 1: Migrate API from AWS to GCP

**Context**: When AWS doesn't provide persistent URLs or has delays.

**Steps**:
1. Set up GCP project (if not exists)
2. Create Terraform configuration
3. Set up GitHub Actions with OIDC
4. Configure secrets in GitHub
5. Deploy infrastructure with Terraform
6. Deploy application via GitHub Actions

**Key files to create**:
- `terraform/main.tf` - Infrastructure
- `.github/workflows/deploy.yml` - CI/CD
- Update `README.md` - Deployment docs

### Task 2: Set Up New Environment

**Pattern for alpha/staging/prod**:
1. Create GCP project: `policyengine-[service]-[env]`
2. Create storage bucket: Match project name (or shortened)
3. Duplicate Terraform configs with env-specific variables
4. Set up separate GitHub workflow or environment
5. Configure environment-specific secrets

### Task 3: Update Cloud Run Configuration

**Common updates**:
```bash
# Update memory/CPU
gcloud run services update policyengine-api \
  --memory 4Gi \
  --cpu 4

# Update environment variables
gcloud run services update policyengine-api \
  --set-env-vars "KEY=value"

# Update timeout
gcloud run services update policyengine-api \
  --timeout 3600
```

**Via Terraform**: Update `main.tf` resource configuration and apply.

## Troubleshooting

### Terraform Issues

**State lock errors**:
```bash
# Force unlock (use carefully)
terraform force-unlock [LOCK_ID]
```

**Import existing resources**:
```bash
# If resource exists but not in state
terraform import google_storage_bucket.main [BUCKET_NAME]
```

**Plan shows unwanted changes**:
- Check provider version compatibility
- Verify variable values
- Review resource attributes vs. current state

### GitHub Actions Issues

**OIDC authentication fails**:
- Verify `id-token: write` permission set
- Check Workload Identity Provider configuration in GCP
- Ensure service account has required roles
- Verify GitHub repo is allowed in workload identity pool

**Deployment fails**:
- Check Cloud Run service logs: `gcloud run logs read`
- Verify container builds successfully
- Check IAM permissions for service account
- Verify region and project ID

### Cloud Run Issues

**Service not accessible**:
- Check IAM policy: `gcloud run services get-iam-policy [SERVICE]`
- Verify public access if needed
- Check VPC connector if using private networking

**High latency**:
- Review container startup time
- Check cold start performance
- Consider minimum instances setting
- Review resource limits (CPU/memory)

## Migration Patterns

### AWS to GCP Migration

When moving from AWS to GCP Cloud Run:

1. **Infrastructure mapping**:
   - AWS Lambda/ECS → GCP Cloud Run
   - AWS S3 → GCP Cloud Storage
   - AWS RDS → GCP Cloud SQL
   - AWS Secrets Manager → GCP Secret Manager

2. **Update code**:
   - Change AWS SDK calls to GCP client libraries
   - Update environment variable names
   - Adjust authentication methods

3. **Configuration**:
   - Port Terraform from AWS provider to GCP
   - Update CI/CD from AWS credentials to GCP OIDC
   - Migrate secrets to new secret management

4. **Testing**:
   - Deploy to alpha/staging environment first
   - Verify all endpoints work
   - Load test if needed
   - Monitor logs and metrics

## Best Practices

### Infrastructure as Code

- **Always use Terraform** for infrastructure changes
- **Version control** all Terraform files
- **Use variables** for environment-specific values
- **Document** any manual changes needed
- **Remote state** for team collaboration (use GCS backend)

### CI/CD

- **Use OIDC** instead of service account keys
- **Test before deploy** in CI pipeline
- **Separate workflows** for different environments
- **Tag images** with commit SHA or version
- **Rollback plan**: Keep previous working images

### Security

- **Least privilege**: Give service accounts minimal permissions
- **No keys in code**: Use Secret Manager or environment variables
- **Public access**: Only if required, consider Cloud Load Balancer + IAP otherwise
- **Audit logs**: Enable Cloud Audit Logs for compliance

### Cost Management

- **Right-size resources**: Don't over-provision CPU/memory
- **Autoscaling**: Set appropriate min/max instances
- **Storage lifecycle**: Delete old data/images
- **Budget alerts**: Set up billing alerts in GCP

## Related Skills

- **policyengine-api-skill** - API service patterns
- **policyengine-standards-skill** - Code and deployment standards
- **policyengine-code-style-skill** - Configuration file formatting

## Resources

**GCP Documentation**:
- Cloud Run: https://cloud.google.com/run/docs
- Workload Identity Federation: https://cloud.google.com/iam/docs/workload-identity-federation
- Terraform Google Provider: https://registry.terraform.io/providers/hashicorp/google/latest/docs

**GitHub Actions**:
- google-github-actions/auth: https://github.com/google-github-actions/auth
- OIDC setup guide: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-google-cloud-platform

**PolicyEngine Examples**:
- Check `policyengine-api-v2` for reference implementation
- Review `policyengine-api-v2-alpha` for GCP Cloud Run patterns
