import os
import shutil
from pathlib import Path
import numpy as np
import SimpleITK as sitk
from typing import Tuple

def delete_make_folder(path: Path):
    """Delete the folder if it exists and create a new one.

    Args:
        path (Path): Path to the folder.
    """
    if path.exists():
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)

def get_img_mask(image_path: str, mask_path: str, logger) -> Tuple[np.ndarray, sitk.Image, np.ndarray]:
    """Load MRI image and mask, returning normalized image array, image object, and mask array."""
    try:
        # Read images
        img_obj, mask_obj = sitk.ReadImage(image_path), sitk.ReadImage(mask_path)

        # Convert to NumPy arrays
        img, mask = sitk.GetArrayFromImage(img_obj), sitk.GetArrayFromImage(mask_obj)

        # Normalize image to [0, 255]
        img = ((img - img.min()) / (img.max() - img.min())).clip(0, 1) * 255

        return img.astype(np.uint8), img_obj, mask.astype(np.uint8)
    except Exception as e:
        logger.error(f"Error processing image and mask: {e}")
        raise

def render_slice(
    img: np.ndarray, mask: np.ndarray, x: int, view: str
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
    if view != "axial":
        slice_img = np.flipud(slice_img)
        slice_mask = np.flipud(slice_mask)
    return slice_img, slice_mask

