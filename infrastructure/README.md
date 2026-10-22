# Infrastructure (AWS reference architecture)

Terraform for the serverless AWS deployment the system was originally built for. **The thesis
project runs locally and does not need any of this** (see the root README). It is kept as the
description of the production architecture and stays valid Terraform (`terraform validate`).

## Architecture

- **Compute:** Lambda functions (Python 3.11): scraper, orchestrator (report generation),
  three read-only API functions and the upload function
- **Storage:** S3 buckets for scraped data, client uploads, reports, the website and artifacts
- **AI:** report generation with Claude via the Anthropic API (`ANTHROPIC_API_KEY`);
  retrieval through an Amazon Bedrock Knowledge Base (Titan embeddings, S3 Vectors)
- **Analytics:** Athena + Glue Catalog over the processed data
- **Distribution:** API Gateway (REST, `modules/api_gateway/specs/openapi.yaml`) and CloudFront
- **Automation:** EventBridge rules (monthly scrape, Knowledge Base sync, report)

## Layout

```
infrastructure/
├── environment/poc/     # the environment: one file per service, locals.tf, variables.tf
└── modules/             # reusable modules (lambda, s3, s3_vectors, api_gateway, bedrock,
                         # athena, eventbridge, iam, cloudfront, cloudwatch_log_groups)
```

Every name is derived from `var.project_prefix` (default `sra-thesis`). Bucket names get a
random suffix (`random_id`) and the account ID comes from `aws_caller_identity`, so nothing
is tied to a specific AWS account.

## Variables

| Variable | Purpose | Default |
|---|---|---|
| `project_prefix` | Prefix of every resource name | `sra-thesis` |
| `aws_region` | Target region (Bedrock + S3 Vectors must be available) | `eu-central-1` |
| `anthropic_api_key` | Claude API key for the orchestrator (sensitive; ends up in state) | — |
| `claude_model` | Claude model for report generation | `claude-sonnet-5-5` |
| `knowledge_base_id` | Bedrock Knowledge Base ID (created manually, see below) | — |
| `frontend_origin` | Website origin allowed by the upload buckets' CORS rules | `http://localhost:3000` |

## Deploying (optional)

1. Create an S3 bucket for the Terraform state and put its name in `environment/poc/tfstate.tf`
   (backend blocks cannot use variables).
2. Build the Lambda packages and upload them to the deployment bucket under the `s3_key`
   used in `lambda.tf`.
3. `cd environment/poc && terraform init && TF_VAR_anthropic_api_key=... terraform apply`
4. Create the Bedrock Knowledge Base in the console (the AWS provider used here does not
   manage Knowledge Bases on S3 Vectors): Titan Text Embeddings v2, the S3 Vectors bucket and
   the raw-data bucket as data source. Set `knowledge_base_id` and apply again.
5. Set `frontend_origin` to the CloudFront URL from the outputs and apply again.
6. Build the frontend with `NEXT_PUBLIC_API_URL=<API Gateway stage URL>` and sync `out/` to
   the website bucket.

The Lambda environment selects the AWS backends (`STORAGE_BACKEND=s3`,
`RETRIEVAL_BACKEND=bedrock`); the same code runs locally with the local backends.

## Original CI/CD

`*/github/workflows/` in each component hold the original per-repository GitHub Actions
pipelines (Terraform plan on feature branches, apply and Lambda/website deploys on merge to
`develop`). They are not active in this repository.
