resource "aws_s3_bucket" "book_keeper_store" {
    bucket = var.book_storage_bucket_name

    tags = {
        Name    = "book-keeper-store"
        project = "book-keeper"
    }
}

resource "aws_s3_bucket" "book_keeper_test" {
    bucket = var.book_storage_test_bucket_name

    tags = {
        Name    = "book-keeper-test"
        project = "book-keeper"
    }
}

resource "aws_s3_bucket" "athena_output_bucket" {
  bucket = var.athena_output_bucket_name

  tags = {
    Name    = "athena-output-bucket-1zxf8478"
    project = "book-keeper"
  }
}
