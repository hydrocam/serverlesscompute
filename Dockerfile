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
