resource "aws_lambda_function" "lambda" {
  function_name = var.function_name
  role          = var.role_arn
  handler       = var.handler
  runtime       = var.runtime
  memory_size   = var.memory_size
  timeout       = var.timeout

  s3_bucket = var.s3_bucket
  s3_key    = var.s3_key

  dynamic "vpc_config" {
    for_each = var.vpc_config == null ? [] : [var.vpc_config]
    content {
      subnet_ids         = vpc_config.value.subnet_ids
      security_group_ids = vpc_config.value.security_group_ids
    }
  }

  environment {
    variables = var.environment_variables
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      handler,
      s3_bucket,
      s3_key,
      layers
    ]
  }
}

resource "aws_lambda_permission" "s3_trigger_permissions" {
  count = length(var.lambda_s3_triggers)
  
  statement_id  = "AllowS3Invoke${count.index}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.lambda_s3_triggers[count.index].bucket_arn
}

resource "aws_s3_bucket_notification" "s3_triggers" {
  count = length(var.lambda_s3_triggers)

  bucket = var.lambda_s3_triggers[count.index].bucket_id

  lambda_function {
    lambda_function_arn = aws_lambda_function.lambda.arn
    events              = var.lambda_s3_triggers[count.index].events
    filter_prefix = var.lambda_s3_triggers[count.index].filter_prefix
    filter_suffix   = var.lambda_s3_triggers[count.index].filter_suffix
  }

  depends_on = [aws_lambda_permission.s3_trigger_permissions]
}