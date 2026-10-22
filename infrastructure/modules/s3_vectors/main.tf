resource "aws_s3vectors_vector_bucket" "this" {
    vector_bucket_name = var.bucket_name

    encryption_configuration {
        sse_type = var.encryption_type
    }
    
    tags = var.tags
}

resource "aws_s3vectors_index" "this" {
    index_name = var.index_name
    vector_bucket_name = aws_s3vectors_vector_bucket.this.vector_bucket_name
    
    data_type = var.index_data_type
    dimension = var.index_dimension
    distance_metric = var.index_distance_metric

    tags = var.tags
}