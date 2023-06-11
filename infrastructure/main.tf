terraform {
  required_version = ">= 0.12"
}

module "s3_buckets" {
    source = "./modules/s3_buckets"
}

module "iam" {
    source = "./modules/iam"
}

module "athena" {
    source = "./modules/athena"

    athena_output_bucket_name = module.s3_buckets.athena_output_bucket_name
}