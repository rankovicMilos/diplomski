module "s3_website_cloudfront" {
  source = "../../modules/cloudfront"

  domain_name      = module.website_bucket.bucket_domain_name
  origin_id        = "S3-Website-Origin"
  is_ipv6_enabled  = true
  target_origin_id = "S3-Website-Origin"
  min_ttl          = 0
  default_ttl      = 3600
  max_ttl          = 86400

  # Logs
  logging_bucket_domain_name = module.cloudfront_logs_bucket.bucket_domain_name
  logging_prefix             = "logs/"

  tags = merge(local.common_tags, { Name = "${local.prefix}-s3-website-cloudfront" })
}