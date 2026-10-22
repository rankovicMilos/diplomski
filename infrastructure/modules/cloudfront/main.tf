resource "aws_cloudfront_distribution" "website" {
    origin {
        domain_name = var.domain_name
        origin_id   = var.origin_id
    }

    enabled = true
    is_ipv6_enabled = var.is_ipv6_enabled
    default_root_object = "index.html"

    default_cache_behavior {
        allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
        cached_methods   = ["GET", "HEAD"]
        target_origin_id = var.target_origin_id

        forwarded_values {
            query_string = false
            cookies {
                forward = "none"
            }
        }

        viewer_protocol_policy = "redirect-to-https"
        min_ttl = var.min_ttl
        default_ttl = var.default_ttl
        max_ttl = var.max_ttl
    }

    custom_error_response {
        error_code            = 403
        response_page_path    = "/index.html"
        response_code         = 200
        error_caching_min_ttl = 0
    }

    custom_error_response {
        error_code            = 404
        response_page_path    = "/index.html"
        response_code         = 200
        error_caching_min_ttl = 0
    }

    viewer_certificate {
        cloudfront_default_certificate = var.default_certificate
    }

    restrictions {
        geo_restriction {
            restriction_type = "none"
        }
    }

    logging_config {
      include_cookies = false
      bucket = var.logging_bucket_domain_name
      prefix = var.logging_prefix
    }

    tags = var.tags
}