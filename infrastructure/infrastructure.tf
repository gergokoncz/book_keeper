# define provider
provider "aws" {
    region = "eu-north-1"
}

# define bucket
resource "aws_s3_bucket" "book_keeper_store" {
    bucket  = "book-keeper-store"

    tags = {
        Name    = "book-keeper-store"
        project = "book-keeper"
    }
}

# define user to access bucket
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
}

resource "aws_iam_policy" "book_keeper_store_policy" {
  name        = "book_keeper_store_policy"
  description = "Full access to book-keeper-store bucket"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::book-keeper-store/*"
    }
  ]
}
EOF
}

resource "aws_iam_policy_attachment" "s3_admin_policy_attachment" {
    name        = "s3_admin_policy_attachment"
    roles       = [aws_iam_role.book_keeper_store_role.name]
    policy_arn  = aws_iam_policy.book_keeper_store_policy.arn  
}

# define user to assume the role
resource "aws_iam_user" "book_keeper_user" {
    name = "book_keeper_user"
}

resource "aws_iam_user_policy_attachment" "book_keeper_user_policy_attachment" {
    user       = aws_iam_user.book_keeper_user.name
    policy_arn = aws_iam_policy.book_keeper_store_policy.arn
}

data "aws_caller_identity" "current" {}