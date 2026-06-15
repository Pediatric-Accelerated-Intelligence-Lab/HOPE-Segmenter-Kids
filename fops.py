import os
import shutil
from pathlib import Path
import numpy as np
import SimpleITK as sitk
from typing import Tuple
from constants import TaskName

def delete_make_folder(path: Path):
    """Delete the folder if it exists and create a new one.

    Args:
        path (Path): Path to the folder.
    """
    if path.exists():
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)

def pad_crop_to_nearest_cube(image, mask):
    # mask get the largest bounding box of non-zero values
    non_zero_indices = np.argwhere(mask > -1)
    if non_zero_indices.size == 0:
        return image, mask  # No cropping needed if mask is empty
    
    # get max length of bounding box
    min_coords = non_zero_indices.min(axis=0)
    max_coords = non_zero_indices.max(axis=0)
    bbox_size = max_coords - min_coords + 1
    max_dim = bbox_size.max()
    # calculate padding/cropping needed to make it a cube
    pad_before = (max_dim - bbox_size) // 2
    pad_after = max_dim - bbox_size - pad_before
    # apply padding/cropping to image, mask, and landmark
    print(f"Padding/Cropping - Before: {bbox_size}, Pad before: {pad_before}, Pad after: {pad_after}")
    def pad_crop(arr):
        print(f"Original shape: {arr.shape}")
        padded = np.pad(arr, [(pad_before[i], pad_after[i]) for i in range(3)], mode='constant')
        print(f"Padded shape: {padded.shape}", f"Min coords: {min_coords}", f"Max dim: {max_dim}")
        return padded[min_coords[0]:min_coords[0]+max_dim, min_coords[1]:min_coords[1]+max_dim, min_coords[2]:min_coords[2]+max_dim]
    return pad_crop(image), pad_crop(mask)

def get_img_mask(image_path: str, mask_path: str, logger) -> Tuple[np.ndarray, sitk.Image, np.ndarray]:
    """Load MRI image and mask, returning normalized image array, image object, and mask array."""
    try:
        # Read images
        img_obj, mask_obj = sitk.ReadImage(image_path), sitk.ReadImage(mask_path)

        # Convert to NumPy arrays
        img, mask = sitk.GetArrayFromImage(img_obj), sitk.GetArrayFromImage(mask_obj)

        img, mask = pad_crop_to_nearest_cube(img, mask)

        # Normalize image to [0, 255]
        img = ((img - img.min()) / (img.max() - img.min())).clip(0, 1) * 255

        return img.astype(np.uint8), img_obj, mask.astype(np.uint8)
    except Exception as e:
        logger.error(f"Error processing image and mask: {e}")
        raise

def render_slice(
    img: np.ndarray, mask: np.ndarray, x: int, view: str, model_docker: str
) -> Tuple[np.ndarray, np.ndarray]:
    """Render a specific slice of the image and mask based on the view.

    Args:
        img (np.ndarray): Normalized image array.
        mask (np.ndarray): Mask array.
        x (int): Slice index.
        view (str): View type ('axial', 'coronal', 'sagittal').

    Returns:
        Tuple[np.ndarray, np.ndarray]: 
            - Slice of the image.
            - Slice of the mask.
    """
    if view == "axial":
        slice_img, slice_mask = img[x, :, :], mask[x, :, :]
    elif view == "coronal":
        slice_img, slice_mask = img[:, x, :], mask[:, x, :]
    elif view == "sagittal":
        slice_img, slice_mask = img[:, :, x], mask[:, :, x]
    else:
        raise ValueError(f"Invalid view type: {view}")

    # Flip the slice images upside down for correct orientation for non axial slices
    if model_docker in {TaskName.peds.value, TaskName.men.value, TaskName.met.value}:
        if view != "axial":
            slice_img = np.flipud(slice_img)
            slice_mask = np.flipud(slice_mask)

    elif model_docker in {TaskName.gli.value, TaskName.ssa.value}:
        slice_img = np.flipud(slice_img)
        slice_mask = np.flipud(slice_mask)

        if view == "sagittal":
            slice_img = np.fliplr(slice_img)
            slice_mask = np.fliplr(slice_mask)
    return slice_img, slice_mask

