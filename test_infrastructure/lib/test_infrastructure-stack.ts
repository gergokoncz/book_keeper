import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as iam from "aws-cdk-lib/aws-iam";
import * as athena from "aws-cdk-lib/aws-athena";
import * as glue from "aws-cdk-lib/aws-glue";

export class TestInfrastructureStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create a S3 buckets

    const testBucket = new s3.Bucket(this, "BookKeeperTestBucket", {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const prodBucket = new s3.Bucket(this, "BookKeeperProdBucket", {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Create IAM users

    const testUser = new iam.User(this, "BookKeeperTestUser");
    const prodUser = new iam.User(this, "BookKeeperProdUser");

    // grant the required permissions to the users

    testBucket.grantReadWrite(testUser, "*");
    testBucket.grantDelete(testUser, "*");

    prodBucket.grantReadWrite(prodUser, "*");
    prodBucket.grantDelete(prodUser, "*");

    testUser.addToPolicy(
      new iam.PolicyStatement({
        actions: ["athena:*"],
        resources: ["*"],
      }),
    );

    prodUser.addToPolicy(
      new iam.PolicyStatement({
        actions: ["athena:*"],
        resources: ["*"],
      }),
    );

    // Formulate output

    new cdk.CfnOutput(this, "TestBucketName", {
      value: testBucket.bucketName,
    });

    new cdk.CfnOutput(this, "ProdBucketName", {
      value: prodBucket.bucketName,
    });

    new cdk.CfnOutput(this, "TestUserName", {
      value: testUser.userName,
    });

    new cdk.CfnOutput(this, "ProdUserName", {
      value: prodUser.userName,
    });
  }
}
