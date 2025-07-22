import torch
from segment_anything import SamPredictor, sam_model_registry
from config import checkpoint_path, model_type, device

def load_model():
    sam_model = sam_model_registry[model_type](checkpoint=None)
    state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
    sam_model.load_state_dict(state_dict, strict=True)
    sam_model.eval()
    sam_model.requires_grad_(False)
    sam_model.to(device)
    return SamPredictor(sam_model)