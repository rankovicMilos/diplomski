module "scraper_lambda_role" {
  source = "../../modules/iam"

  role_name            = "${local.prefix}-scraper-lambda-execution-role"
  assume_role_services = ["lambda.amazonaws.com"]
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  inline_policies = [
    jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "s3:PutObject",
            "s3:GetObject",
            "s3:HeadObject",
            "s3:ListBucket"
          ]
          Resource = [
            module.raw_data_staging_bucket.bucket_arn,
            "${module.raw_data_staging_bucket.bucket_arn}/*"
          ]
        }
      ]
    })
  ]

  tags = merge(local.common_tags, { Name = "${local.prefix}-scraper-lambda-execution-role" })
}

module "trigger_upload_lambda_role" {
  source = "../../modules/iam"

  role_name            = "${local.prefix}-trigger-upload-lambda-execution-role"
  assume_role_services = ["lambda.amazonaws.com"]
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  inline_policies = [
    jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "s3:PutObject",
            "s3:ListBucket",
            "s3:GetObject"
          ]
          Resource = [
            module.raw_data_staging_bucket.bucket_arn,
            "${module.raw_data_staging_bucket.bucket_arn}/*",
            module.orchestrator_data.bucket_arn,
            "${module.orchestrator_data.bucket_arn}/*"
          ]
        }
      ]
    })
  ]

  tags = merge(local.common_tags, { Name = "${local.prefix}-trigger-upload-lambda-execution-role" })
}

module "orchestrator_lambda_role" {
  source = "../../modules/iam"

  role_name            = "${local.prefix}-orchestrator-lambda-execution-role"
  assume_role_services = ["lambda.amazonaws.com"]
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  inline_policies = [
    jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "s3:PutObject",
            "s3:ListBucket",
            "s3:GetObject"
          ]
          Resource = [
            module.orchestrator_output_bucket.bucket_arn,
            "${module.orchestrator_output_bucket.bucket_arn}/*"
          ]
        },
        {
          Effect = "Allow"
          Action = [
            "s3:GetObject",
            "s3:ListBucket"
          ]
          Resource = [
            module.raw_data_staging_bucket.bucket_arn,
            "${module.raw_data_staging_bucket.bucket_arn}/*",
            module.orchestrator_data.bucket_arn,
            "${module.orchestrator_data.bucket_arn}/*"
          ]
        },
        {
          Effect = "Allow"
          Action = [
            "bedrock:InvokeModel",
            "bedrock:InvokeModelWithResponseStream",
            "bedrock:GetInferenceProfile"
          ]
          Resource = [
            module.bedrock.inference_profile_model_arn,
            "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0"
          ]
        },
        {
          Effect = "Allow"
          Action = [
            "bedrock:RetrieveAndGenerateStream",
            "bedrock:RetrieveAndGenerate",
            "bedrock:Retrieve"
          ]
          Resource = [
            "arn:aws:bedrock:eu-central-1:${local.account_id}:knowledge-base/${var.knowledge_base_id}"
          ]
        },
        {
          Effect = "Allow"
          Action = [
            "bedrock:InvokeAgent"
          ]
          Resource = [
            module.bedrock.bedrock_agent_arn
          ]
        }
      ]
    })
  ]

  tags = merge(local.common_tags, { Name = "${local.prefix}-orchestrator-lambda-execution-role" })
}

module "get_analyses_lambda_role" {
  source = "../../modules/iam"

  role_name            = "${local.prefix}-get-analyses-lambda-execution-role"
  assume_role_services = ["lambda.amazonaws.com"]
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  inline_policies = [
    jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "s3:GetObject",
            "s3:ListBucket"
          ]
          Resource = [
            module.orchestrator_output_bucket.bucket_arn,
            "${module.orchestrator_output_bucket.bucket_arn}/*"
          ]
        }
      ]
    })
  ]

  tags = merge(local.common_tags, { Name = "${local.prefix}-get-analyses-lambda-execution-role" })
}

module "get_analyses_by_category_lambda_role" {
  source = "../../modules/iam"

  role_name            = "${local.prefix}-get-analyses-by-category-lambda-execution-role"
  assume_role_services = ["lambda.amazonaws.com"]
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  inline_policies = [
    jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "s3:GetObject",
            "s3:ListBucket"
          ]
          Resource = [
            module.orchestrator_output_bucket.bucket_arn,
            "${module.orchestrator_output_bucket.bucket_arn}/*"
          ]
        }
      ]
    })
  ]

  tags = merge(local.common_tags, { Name = "${local.prefix}-get-analyses-by-category-lambda-execution-role" })
}

module "bedrock_kb_execution_role" {
  source = "../../modules/iam"

  role_name            = "${local.prefix}-bedrock-kb-execution-role"
  assume_role_services = ["bedrock.amazonaws.com"]
  managed_policy_arns  = []

  inline_policies = [
    jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Action   = "bedrock:InvokeModel"
          Effect   = "Allow"
          Resource = module.bedrock.bedrock_embedding_agent_arn
        },
        {
          Effect = "Allow"
          Action = [
            "bedrock:InvokeModel*",
            "bedrock:CreateInferenceProfile"
          ]
          Resource = [
            module.bedrock.bedrock_agent_arn,
            "arn:aws:bedrock:eu-central-1:${local.account_id}:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0",
            "arn:aws:bedrock:*:*:application-inference-profile/*"
          ]
        },
        {
          Effect = "Allow"
          Action = [
            "bedrock:GetInferenceProfile",
            "bedrock:ListInferenceProfiles"
          ]
          Resource = [
            module.bedrock.bedrock_agent_arn,
            "arn:aws:bedrock:eu-central-1:${local.account_id}:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0",
            "arn:aws:bedrock:*:*:application-inference-profile/*"
          ]
        },
        {
          Effect = "Allow",
          Action = [
            "s3:GetObject",
            "s3:ListBucket"
          ]
          Resource = [
            module.benchmark_dataset_bucket.bucket_arn,
            "${module.benchmark_dataset_bucket.bucket_arn}/*",
            module.raw_data_staging_bucket.bucket_arn,
            "${module.raw_data_staging_bucket.bucket_arn}/*"
          ]
        },
        {
          Effect = "Allow",
          Action = [
            "s3vectors:ListIndexes",
            "s3vectors:ListVectors",
            "s3vectors:GetIndex",
            "s3vectors:GetVectors",
            "s3vectors:QueryVectors",
            "s3vectors:CreateIndex",
            "s3vectors:DeleteIndex",
            "s3vectors:PutVectors",
            "s3vectors:DeleteVectors"
          ]
          Resource = [
            "${module.kb_vector_bucket.bucket_arn}/*",
            module.kb_vector_bucket.bucket_arn
          ]
        }
      ]
    })
  ]

  tags = merge(local.common_tags, { Name = "${local.prefix}-bedrock-agent-role" })
}

module "get_client_analyses_lambda_role" {
  source = "../../modules/iam"

  role_name            = "${local.prefix}-get-client-analyses-lambda-execution-role"
  assume_role_services = ["lambda.amazonaws.com"]
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]
  inline_policies = [
    jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "s3:GetObject",
            "s3:ListBucket"
          ]
          Resource = [
            module.orchestrator_output_bucket.bucket_arn,
            "${module.orchestrator_output_bucket.bucket_arn}/*"
          ]
        }
      ]
    })
  ]

  tags = merge(local.common_tags, { Name = "${local.prefix}-get-client-analyses-lambda-execution-role" })
}

module "api_gw_cloudwatch_role" {
  source = "../../modules/iam"

  role_name            = "${local.prefix}-api-gw-cloudwatch-role"
  assume_role_services = ["apigateway.amazonaws.com"]
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
  ]

  tags = merge(local.common_tags, { Name = "${local.prefix}-api-gw-cloudwatch-role" })
}

module "athena_role" {
  source = "../../modules/iam"

  role_name            = "${local.prefix}-athena-execution-role"
  assume_role_services = ["athena.amazonaws.com"]
  managed_policy_arns  = []
  inline_policies = [
    jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "s3:PutObject",
            "s3:GetObject",
            "s3:ListBucket"
          ]
          Resource = [
            module.athena_query_results_bucket.bucket_arn,
            "${module.athena_query_results_bucket.bucket_arn}/*",
            module.cloudfront_logs_bucket.bucket_arn,
            "${module.cloudfront_logs_bucket.bucket_arn}/*"
          ]
        }
      ]
    })
  ]
}

module "kb_sync_lambda_role" {
  source = "../../modules/iam"

  role_name            = "${local.prefix}-sync-kb-lambda-execution-role"
  assume_role_services = ["lambda.amazonaws.com"]
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  inline_policies = [
    jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "bedrock:StartIngestionJob"
          ]
          Resource = [
            "arn:aws:bedrock:eu-central-1:${local.account_id}:knowledge-base/${var.knowledge_base_id}"
          ]
        }
      ]
    })
  ]
}