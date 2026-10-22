output "bucket_arn" {
  description = "The ARN of the S3 Vectors bucket"
  value       = aws_s3vectors_vector_bucket.this.vector_bucket_arn
}