variable "log_group_name" {
  description = "The name of the CloudWatch Log Group"
  type        = string
}

variable "retention_in_days" {
  description = "The number of days to retain log events in the specified log group"
  type        = number
  default     = 30
}

variable "tags" {
  description = "A map of tags to assign to the log group"
  type        = map(string)
  default     = {}
}