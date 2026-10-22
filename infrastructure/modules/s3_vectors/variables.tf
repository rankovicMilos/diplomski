variable "bucket_name" {
  type        = string
}

variable "encryption_type" {
  type        = string
  default     = "AES256"
}

variable "tags" {
  type        = map(string)
  default     = {}
}

variable "index_name" {
  type        = string
}

variable "index_data_type" {
  type        = string
  default = "float32"
}

variable "index_dimension" {
  type        = number
  default = 1024
}

variable "index_distance_metric" {
  type        = string
  default = "cosine"
}