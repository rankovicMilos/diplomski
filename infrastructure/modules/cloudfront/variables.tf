variable "domain_name" {
    description = "The domain name of the S3 bucket used for website hosting."
    type        = string
}

variable "origin_id" {
    description = "The ID of the S3 bucket used for website hosting."
    type        = string
}

variable "is_ipv6_enabled" {
    description = "Boolean to enable or disable IPv6 for CloudFront distribution."
    type        = bool
    default     = true
}

variable "target_origin_id" {
    description = "The ID of the origin that CloudFront routes requests to."
    type        = string
}

variable "min_ttl" {
    description = "The minimum amount of time that an object is cached by CloudFront."
    type        = number
    default     = 0
}

variable "default_ttl" {
    description = "The default amount of time that an object is cached by CloudFront."
    type        = number
    default     = 3600
}

variable "max_ttl" {
    description = "The maximum amount of time that an object is cached by CloudFront."
    type        = number
    default     = 86400
}

variable "cloudfront_default_certificate" {
    description = "Boolean to use the default CloudFront certificate."
    type        = bool
    default     = true
}

variable "tags" {
    description = "A map of tags to assign to the CloudFront distribution."
    type        = map(string)
    default     = {}
}

variable "default_certificate" {
    description = "Boolean to use the default CloudFront certificate."
    type        = bool
    default     = true
}

variable "logging_bucket_domain_name" {
    description = "The domain name of the S3 bucket for CloudFront logs."
    type        = string
}

variable "logging_prefix" {
    description = "The prefix for CloudFront logs in the S3 bucket."
    type        = string
    default     = "cloudfront-logs/"
}