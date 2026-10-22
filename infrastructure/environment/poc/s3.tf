module "website_bucket" {
  source = "../../modules/s3"

  bucket_name = "${local.prefix}-website-bucket-${local.bucket_suffix}"

  create_public_access_block = true
  block_public_acls          = false
  block_public_policy        = false
  ignore_public_acls         = false
  restrict_public_buckets    = false

  attach_policy = true
  bucket_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadGetObject"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "arn:aws:s3:::${local.prefix}-website-bucket-${local.bucket_suffix}/*"
    }]
  })

  website      = true
  index_suffix = "index.html"
  error_key    = "error.html"

  tags = merge(local.common_tags, { Name = "${local.prefix}-website-bucket-${local.bucket_suffix}" })
}


module "orchestrator_output_bucket" {
  source = "../../modules/s3"

  bucket_name = "${local.prefix}-orchestrator-output-bucket-${local.bucket_suffix}"

  tags = merge(local.common_tags, { Name = "${local.prefix}-orchestrator-output-bucket-${local.bucket_suffix}" })
}

module "benchmark_dataset_bucket" {
  source = "../../modules/s3"

  bucket_name = "${local.prefix}-benchmark-dataset-bucket-${local.bucket_suffix}"

  tags = merge(local.common_tags, { Name = "${local.prefix}-benchmark-dataset-bucket-${local.bucket_suffix}" })
}

module "raw_data_staging_bucket" {
  source = "../../modules/s3"

  bucket_name = "${local.prefix}-raw-data-staging-bucket-${local.bucket_suffix}"

  enable_cors = true

  cors_allowed_headers = ["Content-Type", "x-amz-meta-original_filename", "x-amz-meta-upload_timestamp"]
  cors_allowed_methods = ["PUT"]
  cors_allowed_origins = ["http://localhost:3002", var.frontend_origin]
  cors_expose_headers  = []
  cors_max_age_seconds = 3000

  tags = merge(local.common_tags, { Name = "${local.prefix}-raw-data-staging-bucket-${local.bucket_suffix}" })
}

module "lambda_deployment_bucket" {
  source = "../../modules/s3"

  bucket_name = "${local.prefix}-lambda-deployment-bucket-${local.bucket_suffix}"

  tags = merge(local.common_tags, { Name = "${local.prefix}-lambda-deployment-bucket-${local.bucket_suffix}" })
}

module "cloudfront_logs_bucket" {
  source = "../../modules/s3"

  bucket_name = "${local.prefix}-cloudfront-logs-bucket-${local.bucket_suffix}"

  create_public_access_block = true

  block_public_acls       = false
  ignore_public_acls      = false
  block_public_policy     = true
  restrict_public_buckets = true

  attach_policy = true
  bucket_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowCloudFrontServiceToWriteLogs"
      Effect = "Allow"
      Principal = {
        "Service" = "delivery.logs.amazonaws.com"
      }
      Action   = "s3:PutObject"
      Resource = "arn:aws:s3:::${local.prefix}-cloudfront-logs-bucket-${local.bucket_suffix}/*"
      Condition = {
        StringEquals = {
          "s3:x-amz-acl" = "bucket-owner-full-control"
        }
      }
    }]
  })

  enable_lifecycle          = true
  lifecycle_rule_id         = "log-expiration-rule"
  lifecycle_prefix          = "logs/"
  lifecycle_expiration_days = 7

  enable_ownership_controls = true

  tags = merge(local.common_tags, { Name = "${local.prefix}-cloudfront-logs-bucket-${local.bucket_suffix}" })
}

module "athena_query_results_bucket" {
  source = "../../modules/s3"

  bucket_name = "${local.prefix}-athena-query-results-bucket-${local.bucket_suffix}"

  enable_lifecycle          = true
  lifecycle_rule_id         = "athena-query-results-expiration-rule"
  lifecycle_prefix          = ""
  lifecycle_expiration_days = 2

  tags = merge(local.common_tags, { Name = "${local.prefix}-athena-query-results-bucket-${local.bucket_suffix}" })
}

module "orchestrator_data" {
  source = "../../modules/s3"

  bucket_name = "${local.prefix}-orchestrator-data-bucket-${local.bucket_suffix}"

  enable_cors = true

  cors_allowed_headers = ["Content-Type", "x-amz-meta-original_filename", "x-amz-meta-upload_timestamp"]
  cors_allowed_methods = ["PUT"]
  cors_allowed_origins = ["http://localhost:3002", var.frontend_origin]
  cors_expose_headers  = []
  cors_max_age_seconds = 3000

  tags = merge(local.common_tags, { Name = "${local.prefix}-orchestrator-data-bucket-${local.bucket_suffix}" })
}

module "sbom_bucket" {
  source = "../../modules/s3"

  bucket_name = "${local.prefix}-sbom-bucket-${local.bucket_suffix}"

  enable_lifecycle = true

  lifecycle_rule_id         = "sbom-expire-retention-7d"
  lifecycle_prefix          = ""
  lifecycle_expiration_days = 7

  tags = merge(local.common_tags, { Name = "${local.prefix}-sbom-bucket-${local.bucket_suffix}" })
}