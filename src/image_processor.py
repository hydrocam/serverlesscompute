import cv2
import numpy as np
from datetime import datetime
from helpers import extract_datetime_from_filename
from s3_utils import upload_to_s3
from config import desired_size, ground_true_path, segmentation_size, regression_model_path
import pickle
from sklearn.ensemble import RandomForestRegressor



trapezium1 = np.array([
    [116, 335],     # top-left
    [328, 548],     # top-right
    [222, 654],     # bottom-right
    [10, 441]       # bottom-left
], dtype=np.int32)
trapezium2 = np.array([[1220, 460], [1480, 340], [1670, 410], [1420, 580]], np.int32)


def calculate_iou(segmented_mask, ground_truth_path=None):
    try:
        if not ground_truth_path:
            return 0
        ground_truth = cv2.imread(ground_truth_path, cv2.IMREAD_GRAYSCALE)
        if ground_truth is None:
            return 0
        if segmented_mask.shape != ground_truth.shape:
            ground_truth = cv2.resize(ground_truth, (segmented_mask.shape[1], segmented_mask.shape[0]),
                                      interpolation=cv2.INTER_NEAREST)
        segmented_binary = (segmented_mask > 0).astype(np.uint8)
        ground_truth_binary = (ground_truth > 0).astype(np.uint8)
        intersection = np.logical_and(segmented_binary, ground_truth_binary).sum()
        union = np.logical_or(segmented_binary, ground_truth_binary).sum()
        return 1 if (intersection / union if union > 0 else 0.0) > 0.9 else 0, round(float(intersection / union),2)
    except:
        return 0, round(float(intersection / union),2)


def process_image(image_path, image_name, predictor, output_bucket):
    image = cv2.imread(image_path)
    if image is None:
        return {"statusCode": 400, "body": {"error": "Invalid image", "image_name": image_name}}

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    if desired_size:
        image_rgb = cv2.resize(image_rgb, desired_size, interpolation=cv2.INTER_LINEAR)

    predictor.set_image(image_rgb)
    masks, _, _ = predictor.predict(point_coords=None, box=None, multimask_output=False)
    binary_mask = (masks[0] > 0).astype(np.uint8)
    binary_mask_resized = cv2.resize(binary_mask, (segmentation_size[1], segmentation_size[0]), interpolation=cv2.INTER_NEAREST)

    trapezium1_mask = np.zeros_like(binary_mask_resized, dtype=np.uint8)
    trapezium2_mask = np.zeros_like(binary_mask_resized, dtype=np.uint8)
    cv2.fillPoly(trapezium1_mask, [trapezium1], 1)
    cv2.fillPoly(trapezium2_mask, [trapezium2], 1)
    roi1_pixels = int(np.sum(binary_mask_resized[trapezium1_mask == 1]))
    roi2_pixels = int(np.sum(binary_mask_resized[trapezium2_mask == 1]))
    with open(regression_model_path, 'rb') as f:
        rf_loaded = pickle.load(f)
    stage_m = rf_loaded.predict(np.array([[roi1_pixels, roi2_pixels]]))
    seg_verify, IoU = calculate_iou(binary_mask_resized, ground_true_path)
    timestamp, year, month = extract_datetime_from_filename(image_name)
    if timestamp is None:
        return {"statusCode": 422, "body": {"error": "Timestamp extraction failed", "image_name": image_name}}

    overlay = cv2.resize(image, (segmentation_size[1], segmentation_size[0]), interpolation=cv2.INTER_LINEAR)
    overlay[binary_mask_resized == 1] = [0, 0, 255]
    cv2.polylines(overlay, [trapezium1], True, (255, 0, 0), 4)
    cv2.polylines(overlay, [trapezium2], True, (255, 0, 0), 4)

    segmented_path = f"/tmp/{image_name.replace('.jpg', '_segmented.png')}"
    segmented_key = f"{year}/{month}/{image_name.replace('.jpg', '_segmented.png')}"
    cv2.imwrite(segmented_path, overlay)

    upload_to_s3(segmented_path, output_bucket, segmented_key)
    segmented_image_url = f"https://{output_bucket}.s3.amazonaws.com/{segmented_key}"

    return {
        "statusCode": 200,
        "body": {
            "message": "Processing successful",
            "timestamp": timestamp,
            "roi": [roi1_pixels, roi2_pixels],
            "segmented_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "segmented_bucket_path": f"{output_bucket}/{segmented_key}",
            "IoU": IoU,
            "Seg_verified": bool(seg_verify),
            "segmented_image_url": segmented_image_url,
            "Stage":round(float(stage_m[0]), 2)
        }
    }
