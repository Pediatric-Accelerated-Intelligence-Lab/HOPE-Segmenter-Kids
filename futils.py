"""
DICOM ↔ NIfTI Conversion Utilities by @aparida12
--------------------------------------------------------------------

This script provides utilities for converting between DICOM and 
NIfTI formats, including:
    - DICOM → NIfTI conversion
    - NIfTI → DICOM image conversion
    - NIfTI segmentation → DICOMSEG conversion
It also verifies data consistency after round-trip conversion.

Dependencies:
    pip install pyplastimatch dicom2nifti nifti2dicom nibabel numpy
"""

import os
import logging
import subprocess
import numpy as np
import nibabel as nib
import dicom2nifti
import pyplastimatch as pypla
from pyplastimatch.utils.install import install_precompiled_binaries

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def dicom_to_nifti(dicom_directory: str, output_folder: str, name: str = "converted.nii.gz") -> str:
    """
    Convert a directory of DICOM files into a single compressed NIfTI file.

    Parameters
    ----------
    dicom_directory : str
        Path to the input DICOM directory.
    output_folder : str
        Directory where the output NIfTI file will be saved.
    name : str, optional
        Desired output NIfTI filename (default: 'converted.nii.gz').

    Returns
    -------
    str
        Path to the converted NIfTI file.
    """
    os.makedirs(output_folder, exist_ok=True)
    logging.info(f"Converting DICOM to NIfTI from: {dicom_directory}")

    dicom2nifti.convert_directory(
        dicom_directory, output_folder, compression=True, reorient=True
    )

    # Rename the generated file to the specified name
    for file in os.listdir(output_folder):
        if file.endswith((".nii", ".nii.gz")):
            src = os.path.join(output_folder, file)
            dst = os.path.join(output_folder, name)
            os.rename(src, dst)
            logging.info(f"Saved NIfTI file: {dst}")
            return dst

    raise FileNotFoundError("No NIfTI file generated during DICOM conversion.")


def nifti_to_dicom(nifti_file: str, dicom_dir: str, patient_name: str = "patient1") -> None:
    """
    Convert a NIfTI file to a directory of DICOM image files using pyplastimatch.

    Parameters
    ----------
    nifti_file : str
        Path to the input NIfTI file.
    dicom_dir : str
        Directory where the output DICOM files will be stored.
    patient_name : str, optional
        Patient name tag to embed in DICOM metadata.
    """
    os.makedirs(dicom_dir, exist_ok=True)
    logging.info(f"Converting NIfTI to DICOM: {nifti_file}")

    convert_args = {
        "input": nifti_file,
        "patient-name": patient_name,
        "output-dicom": dicom_dir,
        "modality": "MR",
    }
    pypla.convert(verbose=True, **convert_args)
    logging.info(f"DICOM series saved to: {dicom_dir}")


def nifti_to_dicom_seg(ref_dicom_dir: str, seg_nifti_file: str, out_dir: str) -> str:
    """
    Convert a segmentation NIfTI file to a DICOM SEG format using nifti2dicom.

    Parameters
    ----------
    ref_dicom_dir : str
        Reference DICOM directory (for spatial and metadata context).
    seg_nifti_file : str
        Path to the segmentation NIfTI file.
    out_dir : str
        Output directory where DICOM SEG will be saved.

    Returns
    -------
    str
        Path to the resulting DICOM SEG file.
    """
    os.makedirs(out_dir, exist_ok=True)
    logging.info(f"Converting segmentation NIfTI to DICOM SEG: {seg_nifti_file}")

    cmd = [
        "nifti2dicom",
        "-d", ref_dicom_dir,
        "-n", seg_nifti_file,
        "-o", out_dir,
        "-j", "./meta.json",
        "-desc", "PAILab BraTs2025 GLI Segmenter",
        "-t", "seg"
    ]

    subprocess.run(cmd, check=True)
    out_path = os.path.join(out_dir, f"{os.path.basename(seg_nifti_file)}.dcm")
    logging.info(f"Segmentation DICOM saved at: {out_path}")
    return out_path

def validate_roundtrip(original_nifti: str, reconverted_nifti: str) -> None:
    """
    Validate that a reconverted NIfTI file is identical to the original.

    Parameters
    ----------
    original_nifti : str
        Path to the original NIfTI file.
    reconverted_nifti : str
        Path to the reconverted NIfTI file.
    """
    logging.info("Validating round-trip NIfTI conversion consistency...")

    original_data = nib.load(original_nifti).get_fdata()
    reconverted_data = nib.load(reconverted_nifti).get_fdata()

    if np.array_equal(original_data, reconverted_data):
        logging.info("Reconverted data matches original.")
    else:
        raise ValueError("Reconverted NIfTI does not match original.")


if __name__ == "__main__":
    install_precompiled_binaries()

    patient_id = "BraTS-GLI-00492-000"
    basepath = "/home/pmilab/Code/BraTS2025-InferApp"
    modalities = ["t1n", "t1c", "t2f", "t2w"]

    # Convert NIfTI to DICOM for each modality
    for modality in modalities:
        nifti_path = os.path.join(basepath, "examples", patient_id, f"{patient_id}-{modality}.nii.gz")
        dicom_out = os.path.join(basepath, "data", "dicom_output", f"{patient_id}-{modality}")
        nifti_to_dicom(nifti_file=nifti_path, dicom_dir=dicom_out, patient_name=patient_id)

    # Convert segmentation NIfTI to DICOM SEG
    seg_path = os.path.join(basepath, "example_outs", f"{patient_id}.nii.gz")
    seg_dicom = nifti_to_dicom_seg(
        ref_dicom_dir=os.path.join(basepath, "data", "dicom_output", f"{patient_id}-t1c"),
        seg_nifti_file=seg_path,
        out_dir=os.path.join(basepath, "data", "dicomseg_output", f"{patient_id}-seg")
    )

    # Convert DICOM back to NIfTI
    reconverted_path = dicom_to_nifti(
        dicom_directory=os.path.join(basepath, "data", "dicom_output", f"{patient_id}-t1c"),
        output_folder=os.path.join(basepath, "data", "nifti_output", f"{patient_id}-t1c"),
        name=f"{patient_id}-t1c.nii.gz"
    )

    # Validate conversion consistency
    original_path = os.path.join(basepath, "examples", patient_id, f"{patient_id}-t1c.nii.gz")
    validate_roundtrip(original_path, reconverted_path)