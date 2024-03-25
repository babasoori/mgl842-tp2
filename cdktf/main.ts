
import * as path from "path";

import {Construct} from "constructs";
import {App, TerraformStack, TerraformAsset, AssetType} from "cdktf";
import { AwsProvider } from "@cdktf/provider-aws/lib/provider";
import { LambdaFunction } from "@cdktf/provider-aws/lib/lambda-function";
import { S3Bucket } from "@cdktf/provider-aws/lib/s3-bucket";
import { S3Object } from "@cdktf/provider-aws/lib/s3-object";
import { IamRolePolicyAttachment } from "@cdktf/provider-aws/lib/iam-role-policy-attachment";
import { IamRole } from "@cdktf/provider-aws/lib/iam-role";

interface LambdaFunctionConfig {
  path: string,
  handler: string,
  runtime: string,
  stageName: string,
  version: string,
};

const lambdaRolePolicy = {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
};

class LambdaStack extends TerraformStack {
  constructor(scope: Construct, name: string, config: LambdaFunctionConfig) {
    super(scope, name);

    new AwsProvider(this, "aws", {
      region: "us-east-1",
    });

    // new random.provider.RandomProvider(this, "random");
    //
    // // Create random value
    // const pet = new random.pet.Pet(this, "random-name", {
    //   length: 2,
    // });

    // Create Lambda executable
    const asset = new TerraformAsset(this, "lambda-asset", {
      path: path.resolve(__dirname, config.path),
      type: AssetType.ARCHIVE, // if left empty it infers directory and file
    });

    // Create unique S3 bucket that hosts Lambda executable
    const bucket = new S3Bucket(this, "bucket", {
      bucketPrefix: "pr-reviewer-v1",
      acl: "private",
    });

    // Upload Lambda zip file to newly created S3 bucket
    const lambdaArchive = new S3Object(this, "lambda-archive", {
      bucket: bucket.bucket,
      key: `${config.version}/${asset.fileName}`,
      source: asset.path, // returns a posix path
    });

    // Create Lambda role
    const role = new IamRole(this, "pr-reviewer-v1-lambda-exec", {
      name: "pr-reviewer-v1-lambda-exec",
      assumeRolePolicy: JSON.stringify(lambdaRolePolicy)
    });

    // Add execution role for lambda to write to CloudWatch logs
    new IamRolePolicyAttachment(this, "lambda-managed-policy", {
      policyArn: 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
      role: role.name
    });

    // Create Lambda function
   new LambdaFunction(this, "pr-reviewer", {
      functionName: "pr-reviewer-v1",
      s3Bucket: bucket.bucket,
      s3Key: lambdaArchive.key,
      handler: config.handler,
      runtime: config.runtime,
      role: role.arn
    });

    // // Create and configure API gateway
    // const api = new aws.apigatewayv2Api.Apigatewayv2Api(this, "api-gw", {
    //   name: name,
    //   protocolType: "HTTP",
    //   target: lambdaFunc.arn
    // });

    // new aws.lambdaPermission.LambdaPermission(this, "apigw-lambda", {
    //   functionName: lambdaFunc.functionName,
    //   action: "lambda:InvokeFunction",
    //   principal: "apigateway.amazonaws.com",
    //   sourceArn: `${api.executionArn}/*/*`,
    // });

    // new TerraformOutput(this, 'url', {
    //   value: api.apiEndpoint
    // });
  }
};

const app = new App();

new LambdaStack(app, 'pr-reviewer-v1', {
  path: "../src",
  handler: "index.handler",
  runtime: "nodejs14.x",
  stageName: "beta",
  version: "v0.0.1"
});


app.synth();