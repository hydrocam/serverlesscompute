import torch
from PIL import Image
import numpy as np
from transformers import SegformerFeatureExtractor, SegformerForSemanticSegmentation
import boto3
from skimage.measure import label, regionprops

# Initialize S3 resource and client for accessing and uploading files
s3 = boto3.resource('s3')
client_s3 = boto3.client('s3')

# Download the model weights from the S3 bucket to a local temporary file
result = client_s3.download_file("<bucketnamewithmodel>", "<epochs>.pth", "/tmp/<epochs>.pth")


def load_model(model_config, weight_path, num_classes=2):
    """
    Load and initialize the Segformer model with pre-trained weights.

    Args:
    - model_config (str): Identifier or path to the model configuration.
    - weight_path (str): Path to the model weights file.
    - num_classes (int): Number of classes for segmentation (default is 2).

    Returns:
    - model (SegformerForSemanticSegmentation): The initialized Segformer model.
    - feature_extractor (SegformerFeatureExtractor): The feature extractor for the model.
    """
    # Load the feature extractor and model configuration from the pre-trained model
    feature_extractor = SegformerFeatureExtractor.from_pretrained(model_config)
    model = SegformerForSemanticSegmentation.from_pretrained(model_config, num_labels=num_classes,
                                                             ignore_mismatched_sizes=True)

    # Load the model weights from the specified file
    model.load_state_dict(torch.load(weight_path, map_location=torch.device('cpu')))
    model.eval()  # Set the model to evaluation mode
    # model.cuda()  # Uncomment if running on GPU

    return model, feature_extractor


def inference(image, model, feature_extractor):
    """
    Perform inference on an input image to obtain the segmentation mask.

    Args:
    - image (PIL.Image.Image): Input image to be segmented.
    - model (SegformerForSemanticSegmentation): The Segformer model for segmentation.
    - feature_extractor (SegformerFeatureExtractor): The feature extractor for preprocessing.

    Returns:
    - largest_mask (np.ndarray): Binary mask of the largest connected region in the segmentation output.
    """
    # Preprocess the image using the feature extractor
    inputs = feature_extractor(images=image, return_tensors="pt")
    pixel_values = inputs["pixel_values"].cpu()

    with torch.no_grad():  # Disable gradient calculation for inference
        outputs = model(pixel_values=pixel_values)

    # Get the logits (predictions) and find the most likely class for each pixel
    logits = outputs.logits
    predictions = logits.argmax(dim=1)
    pred_mask = predictions.squeeze().cpu().numpy()

    # Label all connected regions in the mask and extract region properties
    labeled_mask = label(pred_mask)
    regions = regionprops(labeled_mask)

    # Find the largest region by area
    largest_region = max(regions, key=lambda r: r.area)

    # Create a binary mask for the largest region
    largest_mask = (labeled_mask == largest_region.label).astype(np.uint8)

    return largest_mask


def overlay_mask_on_image(image, mask, opacity=128):
    """
    Overlay the segmentation mask onto the original image.

    Args:
    - image (PIL.Image.Image): Original image.
    - mask (np.ndarray): Segmentation mask to overlay.
    - opacity (int): Opacity of the overlay mask (0-255).

    Returns:
    - combined_image (PIL.Image.Image): Image with the mask overlaid.
    """
    # Ensure opacity is within the valid range [0, 255]
    opacity = max(0, min(255, opacity))

    # Ensure the mask is in the correct data type
    mask = mask.astype(np.uint8)

    # Resize the mask to match the original image size
    resized_mask = Image.fromarray(mask).resize(image.size, resample=Image.NEAREST)

    # Create an RGBA version of the mask with a green color and the specified opacity
    rgba_mask = np.zeros((image.size[1], image.size[0], 4), dtype=np.uint8)  # Create an empty RGBA array
    rgba_mask[..., :3] = np.array([0, 255, 0])  # Set RGB channels to green color
    rgba_mask[..., 3] = (np.array(resized_mask) * opacity)  # Set alpha channel based on mask and opacity

    # Convert the original image to RGBA format
    rgba_image = np.array(image.convert("RGBA"))

    # Overlay the mask on the image using alpha compositing
    combined_image = Image.alpha_composite(Image.fromarray(rgba_image), Image.fromarray(rgba_mask))

    return combined_image


def readImageFromBucket(key, bucket_name):
    """
    Read an image from an S3 bucket.

    Args:
    - key (str): The key of the image object in the bucket.
    - bucket_name (str): The name of the S3 bucket.

    Returns:
    - image (PIL.Image.Image): The image object.
    """
    bucket = s3.Bucket(bucket_name)
    obj = bucket.Object(key)
    response = obj.get()
    return Image.open(response['Body']).convert("RGB")


def lambda_handler(event, context):
    """
    AWS Lambda handler function.

    Args:
    - event (dict): The event data from S3 trigger.
    - context (LambdaContext): The context object (not used here).

    Returns:
    - None
    """
    # Extract bucket name and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Read the image from the S3 bucket
    image = readImageFromBucket(key, bucket_name)

    # Load the model configuration and weights
    model_config = "nvidia/segformer-b5-finetuned-ade-640-640"
    weight_path = "/tmp/segformer_epoch29.pth"
    model, feature_extractor = load_model(model_config, weight_path, num_classes=2)

    # Perform image segmentation
    pred_mask = inference(image, model, feature_extractor)

    # Overlay the segmentation mask on the original image
    combined_image = overlay_mask_on_image(image, pred_mask)

    # Save the combined image to a temporary file
    temp_save_path = "/tmp/combined_image.png"
    combined_image.save(temp_save_path)

    # Upload the processed image to a new S3 bucket
    new_bucket_name = "<buckettosavesegmentedimages>"
    client_s3.upload_file(temp_save_path, new_bucket_name, key)
