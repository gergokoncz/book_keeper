variable "book_storage_bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
  default     = "book-keeper-store-bucket"
}

variable "athena_output_bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
  default     = "athena-output-bucket-1zxf84bck"
}