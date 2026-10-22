variable "role_name" {
  description = "The name of the IAM role."
  type        = string
}

variable "tags" {
  description = "A map of tags to assign to the IAM role."
  type        = map(string)
  default     = {}
}

variable "assume_role_services" {
  description = "A list of AWS services that can assume this role."
  type        = list(string)
}

variable "managed_policy_arns" {
  description = "ARNS of the managed policies to attach to the IAM role."
  type        = list(string)
  default     = []
}

variable "inline_policies" {
  description = "List of JSON strings representing IAM inline policies"
  type        = list(string)
  default     = []
}