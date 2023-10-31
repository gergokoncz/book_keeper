import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as iam from "aws-cdk-lib/aws-iam";
import * as athena from "aws-cdk-lib/aws-athena";
import * as glue from "aws-cdk-lib/aws-glue";

export class TestInfrastructureStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create an S3 buckets

    const testBucket = new s3.Bucket(this, "BookKeeperTestBucket", {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Create IAM users

    const testUser = new iam.User(this, "BookKeeperTestUser");

    testBucket.grantReadWrite(testUser, "*");
    testBucket.grantDelete(testUser, "*");

    testUser.addToPolicy(
      new iam.PolicyStatement({
        actions: ["athena:*"],
        resources: ["*"],
      }),
    );

    new cdk.CfnOutput(this, "TestBucketName", {
      value: testBucket.bucketName,
    });

    new cdk.CfnOutput(this, "TestUserName", {
      value: testUser.userName,
    });
  }
}
