data "aws_caller_identity" "current" {}

# define user
resource "aws_iam_user" "book_keeper_user" {
    name = "book_keeper_user"
    tags = {
        project = "book-keeper"
    }
}

# define role
resource "aws_iam_role" "book_keeper_store_role" {
    name = "book_keeper_store_role"

    assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "s3.amazonaws.com"
            },
            "Effect": "Allow"
        }
    ]
}
EOF
    tags = {
        project = "book-keeper"
    }
}

## s3 policy

resource "aws_iam_policy" "book_keeper_store_policy" {
    name        = "book-keeper-store-policy"
    description = "Full access to book-keeper-store bucket"

    policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:ListObjectsV2"
      ],
      "Resource": [
        "arn:aws:s3:::book-keeper-store-bucket",
        "arn:aws:s3:::book-keeper-store-bucket/*",
        "arn:aws:s3:::book-keeper-test-bucket",
        "arn:aws:s3:::book-keeper-test-bucket/*"
      ]
    },
        {
      "Sid": "AllowS3BucketCreation",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket"
      ],
      "Resource": [
        "arn:aws:s3:::*"
      ]
    },
    {
      "Sid": "AllowS3AdminAccess",
      "Effect": "Allow",
      "Action": [
        "s3:*"
      ],
      "Resource": [
        "arn:aws:s3:::*",
        "arn:aws:s3:::*/*"
      ]
    }
  ]
}
EOF
    tags = {
        project = "book-keeper"
    }
}

resource "aws_iam_policy_attachment" "s3_admin_policy_attachment" {
    name        = "s3_admin_policy_attachment"
    roles       = [aws_iam_role.book_keeper_store_role.name]
    policy_arn  = aws_iam_policy.book_keeper_store_policy.arn
}

resource "aws_iam_user_policy_attachment" "book_keeper_s3_policy_attachment" {
    user       = aws_iam_user.book_keeper_user.name
    policy_arn = aws_iam_policy.book_keeper_store_policy.arn
}

## athena policy

resource "aws_iam_policy" "athena_query_execution_policy" {
  name        = "athena-query-execution-policy"
  description = "Allows the user to execute Athena queries"
  policy      = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAthenaQueryExecution",
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:GetQueryExecutionInput",
        "athena:GetWorkGroup",
        "athena:ListQueryExecutions"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowGlueTableManagement",
      "Effect": "Allow",
      "Action": [
        "glue:GetTable",
        "glue:CreateTable",
        "glue:DeleteTable",
        "glue:BatchCreatePartition",
        "glue:BatchDeletePartition",
        "glue:UpdateTable",
        "glue:GetPartitions"
      ],
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_policy_attachment" "athena_query_execution_attachment" {
  name       = "athena-query-execution-attachment"
  policy_arn = aws_iam_policy.athena_query_execution_policy.arn
  users      = [aws_iam_user.book_keeper_user.name]
}

resource "aws_iam_user_policy_attachment" "book_keeper_athena_policy_attachment" {
    user       = aws_iam_user.book_keeper_user.name
    policy_arn = aws_iam_policy.athena_query_execution_policy.arn
}
