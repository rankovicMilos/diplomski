variable "function_name" { 
    type = string 
}

variable "role_arn" {
     type = string
}

variable "handler" { 
    type = string 
}

variable "runtime" { 
    type = string
}

variable "memory_size" { 
    type = number
    default = 128 
}

variable "timeout" {
    type = number 
    default = 360
}

variable "s3_bucket" {
     type = string 
}

variable "s3_key" {
     type = string 
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "vpc_config" {
  type = object({
    subnet_ids         = list(string)
    security_group_ids = list(string)
  })
  default = null
}

variable "lambda_s3_triggers" {
  type = list(object({
    bucket_arn    = string
    bucket_id     = string
    events        = list(string)
    filter_prefix = optional(string)
    filter_suffix = optional(string)
  }))
  default = []
}