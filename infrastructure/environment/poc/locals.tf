data "aws_caller_identity" "current" {}

# S3 bucket names are global: a random suffix keeps them unique per deployment
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

locals {
  prefix        = var.project_prefix
  bucket_suffix = random_id.bucket_suffix.hex
  account_id    = data.aws_caller_identity.current.account_id
}
