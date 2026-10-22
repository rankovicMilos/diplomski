variable "glue_catalog_database_name" {
  description = "The name of the Glue Catalog Database to be created for Athena."
  type        = string
}

variable "athena_workgroup_name" {
  description = "The name of the Athena Workgroup to be created."
  type        = string
}

variable "query_results_s3_location" {
  description = "The S3 location where Athena query results will be stored."
  type        = string
}

variable "glue_catalog_tags" {
  description = "A map of tags to assign to the Athena Glue Catalog Database."
  type        = map(string)
  default     = {}
}

variable "athena_workgroup_tags" {
  description = "A map of tags to assign to the Athena Workgroup."
  type        = map(string)
  default     = {}
}