# serverlesscompute
Code for automated extraction of hydrologically relevant information from images and videos using serverless computing.

# Building a Lambda Function with Container Image using AWS CLI

This guide will walk you through the process of building a Lambda function with a container image using AWS CLI in the command line. Before proceeding, ensure that you have Docker installed on your local machine and AWS CLI configured with appropriate permissions.

## Prerequisites

- Docker installed on your local machine
- AWS CLI configured with appropriate permissions
- Dockerfile for building the container image
- Requirements file containing dependencies for your Lambda function
- Lambda function code

## Steps

1. **Write your Lambda function code**: Write your Lambda function code and save it in a directory along with your Dockerfile and requirements file.

2. **Navigate to the Lambda directory**: Open your terminal or command prompt and navigate to the directory where your Lambda function code, Dockerfile, and requirements file are located.

    ```bash
    git clone https://github.com/hydrocam/serverlesscompute
    cd serverlesscompute
    aws configure
    AWS Access Key ID [None]: YOUR_ACCESS_KEY_ID
    AWS Secret Access Key [None]: YOUR_SECRET_ACCESS_KEY
    Default region name [None]: YOUR_PREFERRED_REGION
    Default output format [None]: json
    ```

3. **Write Dockerfile**: Create a Dockerfile in the same directory as your Lambda function code. The Dockerfile specifies the environment and dependencies required for your Lambda function.

    Example Dockerfile:
    ```
    # Pull the base image with python 3.10 as a runtime for your Lambda
    FROM public.ecr.aws/lambda/python:3.10


    # Copy the earlier created requirements.txt file to the container
    COPY requirements.txt ./

    # Install the python requirements from requirements.txt
    RUN python3.10 -m pip install -r requirements.txt

    # Copy the earlier created app.py file to the container
    COPY app.py ./

    # Set the CMD to your handler
    CMD ["app.lambda_handler"]
    ```

4. **Build the Docker image**: Use Docker to build the container image for your Lambda function.

    ```bash
    docker build -t <image-name> .
    ```

5. **Tag the Docker image**: Tag the Docker image with the Amazon ECR repository URI where you'll push the image.

    ```bash
    docker tag <image-name> <aws-account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:lambda-function
    ```

6. **Login to Amazon ECR**: Use the AWS CLI to authenticate Docker to your Amazon ECR registry.

    ```bash
    aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<region>.amazonaws.com
    ```

7. **Push the Docker image to Amazon ECR**: Push the Docker image to your Amazon ECR repository.

    ```bash
    docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:lambda-function
    ```

8. **Create Lambda function**: Use the AWS CLI to create the Lambda function with the container image.

    ```bash
    aws lambda create-function \
    --function-name <function-name> \
    --package-type Image \
    --code ImageUri=<aws-account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:lambda-function \
    --role <role-arn> \
    --memory-size <memory-size> \
    --timeout <timeout> \
    --region <region>
    ```
9. **Add an S3 Bucket Trigger to Lambda Function**: To add an S3 bucket trigger so that your Lambda function is invoked when a new object is added to the bucket, use the aws s3api put-bucket-notification-configuration command
  
    ```bash
      aws s3api put-bucket-notification-configuration \
        --bucket <bucket-name> \
        --notification-configuration '{
            "LambdaFunctionConfigurations": [
                {
                    "LambdaFunctionArn": "arn:aws:lambda:<region>:<aws-account-id>:function:<function-name>",
                    "Events": ["s3:ObjectCreated:*"]
                }
            ]
        }'

    ```
10. **Add Permission for S3 to Invoke Lambda**: Finally, you need to grant the S3 bucket permission to invoke your Lambda function. Use the aws lambda add-permission command:
    
    ```bash
    aws lambda add-permission \
        --function-name <function-name> \
        --principal s3.amazonaws.com \
        --statement-id <unique-statement-id> \
        --action lambda:InvokeFunction \
        --source-arn arn:aws:s3:::<bucket-name> \
        --source-account <aws-account-id>
     ```
