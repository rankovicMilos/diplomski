variable "rule_name" {
    description = "The name of the CloudWatch Event rule."
    type        = string
}

variable "rule_description" {
    description = "The description of the CloudWatch Event rule."
    type        = string
    default     = ""
}

variable "schedule_expression" {
    description = "The scheduling expression that determines when the rule triggers."
    type        = string
}

variable "tags" {
    description = "A map of tags to assign to the CloudWatch Event rule."
    type        = map(string)
    default     = {}
}

variable "enable_target" {
    description = "Whether to enable the target for the CloudWatch Event rule."
    type        = bool
    default     = false
}

variable "target_arn" {
    description = "The ARN of the target to be invoked when the rule is triggered."
    type        = string
    default     = ""
}

variable "lambda_function_name" {
    description = "The name of the Lambda function to grant permission to be invoked by the CloudWatch Event rule."
    type        = string
    default     = ""
}

variable "target_input" {
    description = "The input to be passed to the target when the rule is triggered."
    type        = string
    default     = ""
}