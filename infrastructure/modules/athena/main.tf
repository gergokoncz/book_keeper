resource "aws_glue_catalog_database" "book_keeper_db" {
    name = "book_keeper"
    description = "Athena Database to store user bookkeeper tables"
    tags = {
        project = "book-keeper"
    }
}

resource "aws_athena_workgroup" "book_keeper_workgroup" {
    name = "book_keeper_workgroup"
    tags = {
        project = "book-keeper"
    }
    configuration {
        result_configuration {
            # output_location = "s3://athena-output-bucket-1zxf8478/"
            output_location = "s3://${var.athena_output_bucket_name}/"
        }
    }
}