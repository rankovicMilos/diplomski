output "log_group_arn" {
    description = "The ARN of the CloudWatch Log Group"
    value       = aws_cloudwatch_log_group.this.arn
}