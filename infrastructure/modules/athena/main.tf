resource "aws_glue_catalog_database" "this" {
  name = var.glue_catalog_database_name

  tags = var.glue_catalog_tags
}

resource "aws_athena_workgroup" "this" {
  name = var.athena_workgroup_name

  configuration {
    result_configuration {
      output_location = var.query_results_s3_location
    }

    enforce_workgroup_configuration = true
  }

  tags = var.athena_workgroup_tags
}