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
    cd Lambda
    ```

3. **Write Dockerfile**: Create a Dockerfile in the same directory as your Lambda function code. The Dockerfile specifies the environment and dependencies required for your Lambda function.

    Example Dockerfile:
    ```
    FROM public.ecr.aws/lambda/python:3.8

    COPY requirements.txt /var/task/

    RUN python3.8 -m pip install -r /var/task/requirements.txt
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

