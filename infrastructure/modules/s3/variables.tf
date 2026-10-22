variable "bucket_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "enable_cors" {
  type    = bool
  default = false
}

variable "cors_allowed_headers" {
  type    = list(string)
  default = ["*"]
}

variable "cors_allowed_methods" {
  type    = list(string)
  default = ["GET", "PUT", "POST", "DELETE", "HEAD"]
}

variable "cors_allowed_origins" {
  type    = list(string)
  default = ["*"]
}

variable "cors_expose_headers" {
  type    = list(string)
  default = []
}

variable "cors_max_age_seconds" {
  type    = number
  default = 3000
}

variable "create_public_access_block" {
  type    = bool
  default = false
}

variable "block_public_acls" {
  type    = bool
  default = true
}

variable "block_public_policy" {
  type    = bool
  default = true
}

variable "ignore_public_acls" {
  type    = bool
  default = true
}

variable "restrict_public_buckets" {
  type    = bool
  default = true
}

variable "attach_policy" {
  type    = bool
  default = false
}

variable "bucket_policy" {
  type    = string
  default = ""
}

variable "website" {
  type    = bool
  default = false
}

variable "index_suffix" {
  type    = string
  default = "index.html"
}

variable "error_key" {
  type    = string
  default = "error.html"
}

variable "enable_lifecycle" {
  type    = bool
  default = false
}

variable "lifecycle_rule_id" {
  type    = string
  default = "log-expiration-rule"
}

variable "lifecycle_prefix" {
  type    = string
  default = "logs/"
}

variable "lifecycle_expiration_days" {
  type    = number
  default = 30
}

variable "enable_ownership_controls" {
  type    = bool
  default = false
}