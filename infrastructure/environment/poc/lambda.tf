module "orchestrator" {
  source = "../../modules/lambda"

  function_name = "${local.prefix}-orchestrator-lambda"
  role_arn      = module.orchestrator_lambda_role.role_arn
  handler       = "src.handlers.orchestrator.lambda_handler"
  runtime       = "python3.11"
  memory_size   = 256
  timeout       = 360
  s3_bucket     = module.lambda_deployment_bucket.bucket_name
  s3_key        = "something.zip"

  environment_variables = {
    STORAGE_BACKEND       = "s3"
    RETRIEVAL_BACKEND     = "bedrock"
    ANTHROPIC_API_KEY     = var.anthropic_api_key
    CLAUDE_MODEL          = var.claude_model
    OUTPUT_BUCKET         = "${local.prefix}-orchestrator-output-bucket-${local.bucket_suffix}"
    CLIENT_DATA_BUCKET    = "${local.prefix}-orchestrator-data-bucket-${local.bucket_suffix}"
    KNOWLEDGE_BASE_ID     = var.knowledge_base_id
    ALLOWED_ORIGIN        = var.frontend_origin
    SOURCES_CONFIG_S3_URI = "s3://${local.prefix}-raw-data-staging-bucket-${local.bucket_suffix}/config/scraper/sources"
  }

  lambda_s3_triggers = [
    {
      bucket_arn    = module.orchestrator_data.bucket_arn
      bucket_id     = module.orchestrator_data.bucket_id
      events        = ["s3:ObjectCreated:Put"]
      filter_prefix = "peer_data/"
    }
  ]

  tags = merge(local.common_tags, { Name = "${local.prefix}-orchestrator-lambda" })
}

module "trigger_upload" {
  source = "../../modules/lambda"

  function_name = "${local.prefix}-trigger-upload-lambda"
  role_arn      = module.trigger_upload_lambda_role.role_arn
  handler       = "src.handlers.ingestion.lambda_handler"
  runtime       = "python3.11"
  memory_size   = 256
  timeout       = 360
  s3_bucket     = module.lambda_deployment_bucket.bucket_name
  s3_key        = "something.zip"

  environment_variables = {
    STORAGE_BACKEND          = "s3"
    ORCHESTRATOR_DATA_BUCKET = "${local.prefix}-orchestrator-data-bucket-${local.bucket_suffix}"
    PRESIGNED_URL_EXPIRATION = "3600"
    ALLOWED_ORIGIN           = var.frontend_origin
  }

  tags = merge(local.common_tags, { Name = "${local.prefix}-trigger-upload-lambda" })
}

module "scraper" {
  source = "../../modules/lambda"

  function_name = "${local.prefix}-scraper-lambda"
  role_arn      = module.scraper_lambda_role.role_arn
  handler       = "src.handlers.scraper.lambda_handler"
  runtime       = "python3.11"
  memory_size   = 1024
  timeout       = 900
  s3_bucket     = module.lambda_deployment_bucket.bucket_name
  s3_key        = "something.zip"

  environment_variables = {
    RAW_DATA_BUCKET       = "${local.prefix}-raw-data-staging-bucket-${local.bucket_suffix}"
    SCRAPER_CONFIG_S3_URI = "s3://${local.prefix}-raw-data-staging-bucket-${local.bucket_suffix}/config/scraper/sources"
  }

  tags = merge(local.common_tags, { Name = "${local.prefix}-scraper-lambda" })
}

module "get_analyses" {
  source = "../../modules/lambda"

  function_name = "${local.prefix}-get-analyses-lambda"
  role_arn      = module.get_analyses_lambda_role.role_arn
  handler       = "src.handlers.orchestrator.getAnalyses"
  runtime       = "python3.11"
  memory_size   = 256
  timeout       = 360
  s3_bucket     = module.lambda_deployment_bucket.bucket_name
  s3_key        = "something.zip"

  environment_variables = {
    OUTPUT_BUCKET = "${local.prefix}-orchestrator-output-bucket-${local.bucket_suffix}"
  }

  tags = merge(local.common_tags, { Name = "${local.prefix}-get-analyses-lambda" })
}

module "get_analyses_by_category" {
  source = "../../modules/lambda"

  function_name = "${local.prefix}-get-analyses-by-category-lambda"
  role_arn      = module.get_analyses_by_category_lambda_role.role_arn
  handler       = "src.handlers.orchestrator.getAnalysisByCategory"
  runtime       = "python3.11"
  memory_size   = 256
  timeout       = 360
  s3_bucket     = module.lambda_deployment_bucket.bucket_name
  s3_key        = "something.zip"

  environment_variables = {
    OUTPUT_BUCKET = "${local.prefix}-orchestrator-output-bucket-${local.bucket_suffix}"
  }

  tags = merge(local.common_tags, { Name = "${local.prefix}-get-analyses-by-category-lambda" })
}

module "get_client_analyses" {
  source = "../../modules/lambda"

  function_name = "${local.prefix}-get-client-analyses-lambda"
  role_arn      = module.get_client_analyses_lambda_role.role_arn
  handler       = "src.handlers.orchestrator.getClientAnalyses"
  runtime       = "python3.11"
  memory_size   = 256
  timeout       = 360
  s3_bucket     = module.lambda_deployment_bucket.bucket_name
  s3_key        = "something.zip"
}

module "kb_sync_lambda" {
  source = "../../modules/lambda"

  function_name = "${local.prefix}-sync-kb-lambda"
  role_arn      = module.kb_sync_lambda_role.role_arn
  handler       = "src.handler.lambda_function.lambda_handler"
  runtime       = "python3.11"
  memory_size   = 256
  timeout       = 360
  s3_bucket     = module.lambda_deployment_bucket.bucket_name
  s3_key        = "something.zip"
}