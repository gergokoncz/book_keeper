resource "aws_s3_bucket" "book_keeper_store" {
    bucket = var.book_storage_bucket_name

    tags = {
        Name    = "book-keeper-store"
        project = "book-keeper"
    }
}

resource "aws_s3_bucket" "athena_output_bucket" {
  bucket = var.athena_output_bucket_name

  tags = {
    Name    = "athena-output-bucket"
    project = "book-keeper"
  }
}