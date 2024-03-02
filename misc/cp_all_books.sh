#!/bin/bash
#aws s3 ls
#aws s3 ls s3://book-keeper-store-bucket/gergokoncz/books/
aws s3 cp s3://book-keeper-store-bucket/gergokoncz/ s3://testinfrastructurestack-bookkeepertestbucket15775-10d3x3rqj0o54/test_data/ --recursive
