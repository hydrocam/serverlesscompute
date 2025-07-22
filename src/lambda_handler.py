from datetime import datetime
import os
from config import output_bucket
from model_loader import load_model
from s3_utils import download_from_s3, get_object_metadata
from image_processor import process_image
from database_utils import write_to_database

# Initialize at cold start
def lambda_handler(event, context):
    try:
        predictor = load_model()
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        image_name = os.path.basename(key)
        image_md5 = record['s3']['object']['eTag']
        original_image_url = f"https://{bucket}.s3.amazonaws.com/{key}"
        image_bucket_path = os.path.join(bucket, key)
        print(f"Image Name: {image_name}")
        event_time = datetime.strptime(record['eventTime'][:-5], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        site_id = key.split("/")[0] if len(key.split("/")) == 4 else bucket.split("-")[0]
        print(f"Event Time: {event_time}, Site ID: {site_id}")
        local_path = f"/tmp/{image_name}"
        metadata = get_object_metadata(bucket, key)
        upload_timestamp = metadata['LastModified'].strftime("%Y-%m-%d %H:%M:%S")
        download_from_s3(bucket, key, local_path)
        response = process_image(local_path, image_name, predictor, output_bucket)
        if response['statusCode'] > 300:
            print(f"Image processing failed: {response}")
            return response
        body = response['body']
        print("Writing to database...")
        inserted_id = write_to_database( timestamp=body['timestamp'],
                                         ROI=body['roi'],
                                         segmented_timestamp=body['segmented_timestamp'],
                                         segmented_bucket_path=body['segmented_bucket_path'],
                                         site_id=site_id,
                                         event_timestamp=event_time,
                                         upload_timestamp=upload_timestamp,
                                         image_bucket_path=image_bucket_path,
                                         image_md5=image_md5,
                                         stage=float(body['Stage']),
                                         iou_score=float(body['IoU']),
                                         seg_verify=bool(body['Seg_verified']),
                                         original_image_url=original_image_url,
                                         segmented_image_url=body['segmented_image_url'])
        return {"statusCode": 200, "body": "Processing completed successfully!", "id": inserted_id}

    except Exception as e:
        print("Exception occurred:")
        print(str(e))
        return {
            "statusCode": 500,
            "body": {
                "error": "Error in Lambda Function",
                "exception": str(e)
            }
        }
