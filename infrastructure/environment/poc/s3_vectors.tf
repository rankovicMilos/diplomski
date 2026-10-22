module "kb_vector_bucket" {
  source = "../../modules/s3_vectors"

  bucket_name     = "${local.prefix}-vector-kb-bucket"
  encryption_type = "AES256"

  index_name            = "${local.prefix}-vector-kb-index"
  index_data_type       = "float32"
  index_dimension       = 1024
  index_distance_metric = "cosine"

  tags = merge(local.common_tags, { Name = "${local.prefix}-vector-kb-bucket-index" })
}