resource "aws_cloudwatch_event_rule" "this" {
    name = var.rule_name
    description = var.rule_description
    schedule_expression = var.schedule_expression

    tags = var.tags
}

resource "aws_cloudwatch_event_target" "this" {
    count = var.enable_target ? 1 : 0
    rule = aws_cloudwatch_event_rule.this.name
    arn = var.target_arn
    target_id = "target-${var.rule_name}"

    input = var.target_input != "" ? var.target_input : null
}

resource "aws_lambda_permission" "this" {
    count = var.enable_target ? 1 : 0
    statement_id = "AllowExecutionFromCloudWatch-${var.rule_name}"
    action = "lambda:InvokeFunction"
    function_name = var.lambda_function_name
    principal = "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.this.arn
}