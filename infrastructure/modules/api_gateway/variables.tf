variable "rest_api_name" {
    description = "The name of the API Gateway REST API."
    type        = string
}

variable "api_stage_name" {
    description = "The name of the API Gateway stage."
    type        = string
}

variable "trigger_upload_lambda_name" {
    description = "The name of the Lambda function to be triggered by API Gateway."
    type        = string
}

variable "orchestrator_lambda_name" {
    description = "The name of the Orchestrator Lambda function."
    type        = string
}

variable "get_analyses_lambda_name" {
    description = "The name of the Get Analyses Lambda function."
    type        = string
}

variable "get_analyses_by_category_lambda_name" {
    description = "The name of the Get Analyses By Category Lambda function."
    type        = string
}

variable "get_client_analyses_lambda_name" {
    description = "The name of the Get Client Analyses Lambda function."
    type        = string
}

variable "log_group_arn" {
    description = "The ARN of the CloudWatch Log Group for API Gateway."
    type        = string
}

variable "api_gw_cloudwatch_role_arn" {
    description = "The ARN of the IAM Role for API Gateway to write logs to CloudWatch."
    type        = string
}