import boto3
s3 = boto3.client("s3")

def download_from_s3(bucket, key, dest_path):
    s3.download_file(bucket, key, dest_path)

def upload_to_s3(local_path, bucket, key):
    s3.upload_file(local_path, bucket, key)

def get_object_metadata(bucket, key):
    return s3.head_object(Bucket=bucket, Key=key)