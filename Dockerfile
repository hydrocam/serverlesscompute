# Use the official AWS Lambda base image for Python 3.11
FROM public.ecr.aws/lambda/python:3.11

# Set the working directory
WORKDIR /

RUN yum install -y git

# Copy the requirements file into the container
COPY requirements.txt ./

# Install the required Python packages
RUN python3.11 -m pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"


# Copy the earlier created app.py file to the container
COPY src/ ${LAMBDA_TASK_ROOT}/
COPY Model/ ${LAMBDA_TASK_ROOT}/model/

# Set the CMD to your handler
CMD ["lambda_handler.lambda_handler"]
