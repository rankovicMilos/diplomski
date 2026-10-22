resource "aws_iam_role" "this" {
    name = var.role_name
    tags = var.tags

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Principal = {
                    Service = var.assume_role_services
                }
                Action = "sts:AssumeRole"
            }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "managed_policies" {
    count      = length(var.managed_policy_arns)
    role       = aws_iam_role.this.name
    policy_arn = var.managed_policy_arns[count.index]
}

resource "aws_iam_role_policy" "inline_policy" {
    count = length(var.inline_policies)
    name  = "${var.role_name}-inline-${count.index + 1}"
    role  = aws_iam_role.this.name

    policy = var.inline_policies[count.index]
}