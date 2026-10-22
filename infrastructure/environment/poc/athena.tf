module "athena" {
  source = "../../modules/athena"

  glue_catalog_database_name = "${replace(local.prefix, "-", "_")}_glue_catalog_db"
  athena_workgroup_name      = "${replace(local.prefix, "-", "_")}_athena_workgroup"
  query_results_s3_location  = "s3://${module.athena_query_results_bucket.bucket_name}/athena-query-results/"
  glue_catalog_tags          = merge(local.common_tags, { Name = "${local.prefix}-glue-catalog-db" })
  athena_workgroup_tags      = merge(local.common_tags, { Name = "${local.prefix}-athena-workgroup" })
}