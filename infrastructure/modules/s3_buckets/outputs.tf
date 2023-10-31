# Output the names of the S3 buckets
output "book_keeper_store_bucket_name" {
  value = aws_s3_bucket.book_keeper_store.id
}

output "book_keeper_test_bucket_name" {
  value = aws_s3_bucket.book_keeper_store.id
}

output "athena_output_bucket_name" {
  value = aws_s3_bucket.athena_output_bucket.id
}
