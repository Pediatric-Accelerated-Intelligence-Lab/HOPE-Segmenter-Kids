import logging
import subprocess
import glob
from pathlib import Path
import numpy as np
import SimpleITK as sitk
import PIL
import gradio as gr
import os
from typing import Tuple, List, Dict, Any
import shutil
import base64


def image_to_base64(image_path:str)-> str:
    """Convert a image to the base64 encoding for display of banner.

    Args:
        image_path (str): path to image.

    Returns:
        str: base64 encoded image
    """

    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    return 'data:image/jpeg;base64,'+encoded_string

# Example usage
image_path = "./app_assets/app_header.png"
logo = image_to_base64(image_path)

# Configure the logger for the module
logger = logging.getLogger(__file__)

# Constants

# Always use a dummy name to maintain anonymity
DUMMY_DIR = "BraTS-PED-00019-000"
DUMMY_FILE_NAMES = {
    modality: f"{DUMMY_DIR}-{modality}.nii.gz"
    for modality in ["t1c", "t2f", "t1n", "t2w"]
}

# Docker image for inference
docker = "aparida12/brats-peds-2024:v20250123"

# Dictionary to store intermediate results and paths
mydict: Dict[str, Any] = {}


def run_inference(
    image_t1c: Path, image_t2f: Path, image_t1n: Path, image_t2w: Path
) -> Tuple[str, str]:
    """Run inference on the provided MRI image paths.

    This function performs the following steps:
    1. Copies the provided MRI images to a temporary input directory.
    2. Removes the original uploaded files.
    3. Executes a Docker container to perform segmentation inference.
    4. Moves the inference output to the designated output directory.

    Args:
        image_t1c (Path): Path to the T1 contrast-enhanced MRI image.
        image_t2f (Path): Path to the T2 FLAIR MRI image.
        image_t1n (Path): Path to the T1 pre-contrast MRI image.
        image_t2w (Path): Path to the T2 weighted MRI image.

    Returns:
        Tuple[str, str]: 
            - Path to the input directory containing copied images.
            - Path to the output segmentation file.

    Raises:
        subprocess.CalledProcessError: If any subprocess command fails during execution.
    """
    # Aggregate image paths into a dictionary
    image_paths = {
        "t1c": image_t1c,
        "t2f": image_t2f,
        "t1n": image_t1n,
        "t2w": image_t2w,
    }
    # remove old cache files 
    # Define and create the input directory
    global mydict
    mydict = {}

    input_path = Path("/tmp/peds-app") / DUMMY_DIR
    if input_path.exists():
        shutil.rmtree(input_path)
    os.makedirs(input_path, exist_ok=True)

    # Define and create the output directory
    output_folder = Path("./segmenter/mlcube/outs")
    for file in output_folder.glob("*.nii.gz"):
        os.remove(file)
    os.makedirs(output_folder, exist_ok=True)
    
    # Define paths for the output segmentation
    output_fname = image_t1c.name.replace("-t1c.nii.gz", "-pred.nii.gz")
    output_path = output_folder / output_fname
    fake_output_path = output_folder / f"{DUMMY_DIR}.nii.gz"

    # MOVE each image to the input directory with the dummy filenames
    for key, file in image_paths.items():
        dummy_file_path = input_path / DUMMY_FILE_NAMES[key]
        shutil.copyfile(file, dummy_file_path)
        
    # Construct the Docker command for inference
    mlcube_cmd = (
        f"docker run --shm-size=2gb --gpus=all "
        f"-v {input_path.parent}:/input/ -v {output_folder.absolute()}:/output "
        f"{docker} infer --data_path /input/ --output_path /output/"
    )
    print(mlcube_cmd)

    # Execute the Docker command
    subprocess.run(mlcube_cmd, shell=True, check=True)

    # Move the fake output to the actual output path
    os.rename(fake_output_path, output_path)

    return str(input_path), str(output_path)


def get_img_mask(
    image_path: str, mask_path: str
) -> Tuple[np.ndarray, sitk.Image, np.ndarray]:
    """Retrieve and normalize image and mask data from file paths.

    This function reads the MRI image and corresponding mask from the provided file paths,
    converts them to NumPy arrays, and normalizes the image data.

    Args:
        image_path (str): Path to the MRI image file.
        mask_path (str): Path to the segmentation mask file.

    Returns:
        Tuple[np.ndarray, sitk.Image, np.ndarray]: 
            - Normalized image array.
            - SimpleITK image object for the MRI image.
            - Mask array.

    Raises:
        Exception: If there is an error reading the image or mask files.
    """
    try:
        # Read the MRI image and mask using SimpleITK
        img_obj = sitk.ReadImage(image_path)
        mask_obj = sitk.ReadImage(mask_path)

        # Convert the images to NumPy arrays for processing
        img = sitk.GetArrayFromImage(img_obj)
        mask = sitk.GetArrayFromImage(mask_obj)

        # Normalize the image data to range [0, 255]
        minval, maxval = np.min(img), np.max(img)
        img = ((img - minval) / (maxval - minval)).clip(0, 1) * 255

        return img, img_obj, mask
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


def check_existing_pred(image_t1c: Path) -> bool:
    """Check if a segmentation prediction already exists for the provided image.

    Args:
        image_t1c (Path): Path to the T1 contrast-enhanced MRI image.

    Returns:
        bool: True if a prediction exists, False otherwise.
    """
    basename = os.path.basename(image_t1c)
    basename_without_ext_and_modality = basename.replace("-t1c.nii.gz", "")
    case_data_dir = os.path.join("./examples_segmented", basename_without_ext_and_modality)
    maybe_mask_path = os.path.join(case_data_dir, basename.replace("-t1c.nii.gz", "-pred.nii.gz"))
    return os.path.exists(maybe_mask_path)


def main_func(
    image_t1c: Path, image_t2f: Path, image_t1n: Path, image_t2w: Path
) -> Tuple[str, str]:
    """Main function to handle segmentation workflow.

    This function orchestrates the entire segmentation process:
    1. Runs inference on the uploaded images.
    2. Processes the output to calculate volumetrics.
    3. Updates the global dictionary with relevant paths and data.

    Args:
        image_t1c (Path): Path to the T1 contrast-enhanced MRI image.
        image_t2f (Path): Path to the T2 FLAIR MRI image.
        image_t1n (Path): Path to the T1 pre-contrast MRI image.
        image_t2w (Path): Path to the T2 weighted MRI image.

    Returns:
        Tuple[str, str]: 
            - Path to the segmentation mask file.
            - Status message with volumetrics.

    Raises:
        subprocess.CalledProcessError: If inference fails.
        Exception: If there is an error during processing.
    """
    print(image_t1c)
    global mydict
    
    if check_existing_pred(image_t1c):
        # Retrieve the existing segmentation mask
        mask_path = os.path.join(
            "./examples_segmented",
            os.path.basename(image_t1c).replace("-t1c.nii.gz", ""),
            os.path.basename(image_t1c).replace("-t1c.nii.gz", "-pred.nii.gz"),
        )
        image_files = [
            os.path.join(
                "./examples_segmented",
                os.path.basename(image_t1c).replace("-t1c.nii.gz", ""),
                os.path.basename(image_t1c).replace("-t1c.nii.gz", f"-{modality}.nii.gz"),
            )
            for modality in ["t1c", "t2f", "t1n", "t2w"]
        ]
        # sleep for 30 seconds
        import time
        time.sleep(15)
    else:
        # Run inference and get paths
        input_path, mask_path = run_inference(
            Path(image_t1c), Path(image_t2f), Path(image_t1n), Path(image_t2w)
        )

        # Retrieve all NIfTI files in the input directory
        image_files = glob.glob(os.path.join(input_path, "*.nii.gz"))
        
    mydict["img_path"] = image_files
    mydict["mask_path"] = mask_path

    # Get image and mask data
    img, img_obj, mask = get_img_mask(image_files[0], mask_path)

    # Store image and mask as uint8 for display
    mydict["img"] = img.astype(np.uint8)
    mydict["mask"] = mask.astype(np.uint8)

    print(img_obj.GetSpacing())
    spacing_tuple = img_obj.GetSpacing()

    # Calculate the multiplier for volume calculation
    multiplier_ml = 0.001 * spacing_tuple[0] * spacing_tuple[1] * spacing_tuple[2]

    # Calculate unique labels and their frequencies
    unique, frequency = np.unique(mask, return_counts=True)
    total_sum = 0

    # Calculate volumetrics for each label
    for lbl, count in zip(unique, frequency):
        ml_vol = multiplier_ml * count
        mydict[f"vol_lbl{int(lbl)}"] = ml_vol
        if lbl != 0:
            total_sum += ml_vol

    mydict["vol_total"] = total_sum

    # Construct the status message
    status_message = (
        f"Segmentation done! Total tumor volume segmented {mydict.get('vol_total', 0):.3f} ml; "
        f"EDEMA(ED) {mydict.get('vol_lbl4', 0):.3f} ml; "
        f"ENHANCING TUMOR(ET) {mydict.get('vol_lbl1', 0):.3f} ml; "
        f"NON-ENHANCING TUMOR CORE(NETC) {mydict.get('vol_lbl2', 0):.3f} ml; "
        f"CYSTIC COMPONENT(CC) {mydict.get('vol_lbl3', 0):.3f} ml"
    )

    return mask_path, status_message


def render(file_to_render: str, x: int, view: str) -> Tuple[PIL.Image.Image, List[Tuple[np.ndarray, str]]]:
    """Render the specified slice of the image with annotations.

    Args:
        file_to_render (str): Type of scan to overlay the segmentation on.
        x (int): Slice index.
        view (str): View type ('axial', 'coronal', 'sagittal').

    Returns:
        Tuple[PIL.Image.Image, List[Tuple[np.ndarray, str]]]: 
            - Rendered image with segmentation overlay.
            - List of annotations for each label.

    Raises:
        ValueError: If the specified file type is not found.
    """
    suffix = {
        "T2 FLAIR": "t2f",
        "native T1": "t1n",
        "post-contrast T1-weighted": "t1c",
        "T2 weighted": "t2w",
    }

    if "img_path" in mydict:
        try:
            # Find the corresponding file based on the selected scan type
            get_file = next(
                file for file in mydict["img_path"] if suffix[file_to_render] in file
            )
        except StopIteration:
            logger.error(f"No file found for scan type: {file_to_render}")
            raise ValueError(f"No file found for scan type: {file_to_render}")

        # Retrieve image and mask data
        img, _, mask = get_img_mask(get_file, mydict["mask_path"])

        # Ensure the slice index is within valid range
        max_index = (
            img.shape[0] - 1
            if view == "axial"
            else (img.shape[1] - 1 if view == "coronal" else img.shape[2] - 1)
        )
        x = max(0, min(x, max_index))

        # Render the specific slice
        slice_img, slice_mask = render_slice(img, mask, x, view)

        # Convert the slice to a PIL Image for display
        im = PIL.Image.fromarray(slice_img.astype(np.uint8))

        # Create annotations based on mask labels
        annotations = [
            (slice_mask == 1, f"ET: {mydict.get('vol_lbl1', 0):.3f} ml"),
            (slice_mask == 2, f"NETC: {mydict.get('vol_lbl2', 0):.3f} ml"),
            (slice_mask == 3, f"CC: {mydict.get('vol_lbl3', 0):.3f} ml"),
            (slice_mask == 4, f"ED: {mydict.get('vol_lbl4', 0):.3f} ml"),
        ]

        return im, annotations
    else:
        # Return an empty image and no annotations if paths are not available
        return PIL.Image.fromarray(np.zeros((10, 10), dtype=np.uint8)), []


def render_axial(file_to_render: str, x: int) -> Tuple[PIL.Image.Image, List[Tuple[np.ndarray, str]]]:
    """Render an axial slice of the image.

    Args:
        file_to_render (str): Type of scan to overlay the segmentation on.
        x (int): Slice index.

    Returns:
        Tuple[PIL.Image.Image, List[Tuple[np.ndarray, str]]]: 
            - Rendered axial image with segmentation.
            - Annotations for each label.
    """
    return render(file_to_render, x, "axial")


def render_coronal(file_to_render: str, x: int) -> Tuple[PIL.Image.Image, List[Tuple[np.ndarray, str]]]:
    """Render a coronal slice of the image.

    Args:
        file_to_render (str): Type of scan to overlay the segmentation on.
        x (int): Slice index.

    Returns:
        Tuple[PIL.Image.Image, List[Tuple[np.ndarray, str]]]: 
            - Rendered coronal image with segmentation.
            - Annotations for each label.
    """
    return render(file_to_render, x, "coronal")


def render_sagittal(file_to_render: str, x: int) -> Tuple[PIL.Image.Image, List[Tuple[np.ndarray, str]]]:
    """Render a sagittal slice of the image.

    Args:
        file_to_render (str): Type of scan to overlay the segmentation on.
        x (int): Slice index.

    Returns:
        Tuple[PIL.Image.Image, List[Tuple[np.ndarray, str]]]: 
            - Rendered sagittal image with segmentation.
            - Annotations for each label.
    """
    return render(file_to_render, x, "sagittal")


# Gradio UI Setup
with gr.Blocks(title="Pediatric Segmenter") as demo:
    # Header
    gr.HTML(
        value=f"<center><font size='6'><bold> Children's National Pediatric Brain Tumor Segmenter</bold></font></center>"
    )
    gr.HTML(
        value=f"<p style='margin-top: 1rem; margin-bottom: 1rem'> <img src='{logo}' alt='Childrens National Logo' style='display: inline-block'/></p>"
    )
    gr.HTML(
        value=f"<justify><font size='4'> Welcome to the pediatric brain tumor segmenter. Partial support for this work is provided by the NIH- National Cancer Institute grant UG3-UH3 CA236536. </font></justify>"
    )

    # File Uploads
    with gr.Row():
        image_t1c = gr.File(
            label="Upload T1 Contrast Enhanced Here:",
            file_types=[".gz"],
        )
        image_t2f = gr.File(
            label="Upload T2 FLAIR Here:", file_types=[".gz"]
        )
        image_t1n = gr.File(
            label="Upload T1 Pre-Contrast Here:", file_types=[".gz"]
        )
        image_t2w = gr.File(
            label="Upload T2 Weighted Here:", file_types=[".gz"]
        )
        mask_path = gr.File(
            label="Upload Segmentation Here:", file_types=[".gz"], visible=False
        )
    with gr.Row():
        with gr.Column():
            pass
        with gr.Column():
            gr.Markdown("#### Please read the [instructions](https://docs.hope4kids.io/HOPE-Segmenter-Kids/) before using the app.")
            enable_checkbox = gr.Checkbox(label="I have read the instructions and accept the terms.", value=False, container=False)
            # enable_checkbox = gr.Checkbox(label="I have read the instructions and accept the terms.", value=False, info="#### Please read the [instructions](https://docs.hope4kids.io/HOPE-Segmenter-Kids/) before using the app.", container=False)
        with gr.Column():
            pass    # Segmentation Button
    with gr.Row():
        with gr.Column():
            gr.Button("", visible=False)  # Spacer
        with gr.Column():
            btn = gr.Button("Start Segmentation", interactive=False)
        with gr.Column():
            gr.Button("", visible=False)  # Spacer

    enable_checkbox.change(
        lambda checked: gr.update(interactive=checked),
        inputs=[enable_checkbox],
        outputs=[btn],
    )

    # Status Output
    with gr.Column():
        out_text = gr.Textbox(
            label="Status", placeholder="Volumetrics will be updated here."
        )

    # Dropdown for Rendering
    with gr.Row():
        with gr.Column():
            gr.Button("", visible=False)  # Spacer
        with gr.Column():
            dropdown_modality = ["T2 FLAIR","native T1", "post-contrast T1-weighted", "T2 weighted"]
            file_to_render = gr.Dropdown(
                dropdown_modality,
                value =  dropdown_modality[0],
                label='Choose the scan to overlay the segmentation on'
            )
        with gr.Column():
            gr.Button("", visible=False)  # Spacer

    # Image Displays
    with gr.Row():
        height = "20vw"
        myimage_axial = gr.AnnotatedImage(label="Axial View", height=height)
        myimage_coronal = gr.AnnotatedImage(label="Coronal View", height=height)
        myimage_sagittal = gr.AnnotatedImage(label="Sagittal View", height=height)

    # Sliders for Slice Selection
    with gr.Row():
        slider_axial = gr.Slider(
            0, 155, step=1, label="Axial Slice", info="Adjust the axial slice."
        )  # Max val needs to be updated by user.
        state_axial = gr.State(value=75)
        slider_coronal = gr.Slider(
            0, 155, step=1, label="Coronal Slice", info="Adjust the coronal slice."
        )  # Max val needs to be updated by user.
        state_coronal = gr.State(value=75)
        slider_sagittal = gr.Slider(
            0, 155, step=1, label="Sagittal Slice", info="Adjust the sagittal slice."
        )  # Max val needs to be updated by user.
        state_sagittal = gr.State(value=75)

    # Segmentation File Download
    with gr.Row():
        mask_file = gr.File(label="Download Segmentation File", height="vw")

    # # Examples Setup
    # example_dir = "./examples"
    # generate_examples =  [os.path.join(example_dir, names) for names in [
    #     'BraTS-PED-00019-000',
    #     'BraTS-PED-00051-000',
    #     'BraTS-PED-00300-000',
    #     'BraTS-PED-00001-000',
    #     'BraTS-PED-00018-000',
    #     'BraTS-PED-00021-000',
    #     'BraTS-PED-00351-000'
    # ]]#sorted(glob.glob(os.path.join(example_dir, "*")))
    # order_list = ["-t1c.nii.gz", "-t2f.nii.gz", "-t1n.nii.gz", "-t2w.nii.gz"]
    # example_list = [
    #     [os.path.join(path, f"{Path(path).name}{ending}") for ending in order_list]
    #     for path in generate_examples
    # ]

    # gr.Examples(
    #     examples=example_list,
    #     inputs=[image_t1c, image_t2f, image_t1n, image_t2w],
    #     outputs=[mask_file, out_text],
    #     fn=main_func,
    #     cache_examples=False,
    #     label="Preloaded BraTS2024 Examples",
    # )
    
    # Segmented Examples Setup
    example_dir_seg = "./examples_segmented"
    generate_examples_segmented =  [os.path.join(example_dir_seg, names) for names in [
        'BraTS-PED-00037-000',
        'BraTS-PED-00060-000',
        'BraTS-PED-00146-000',
        'BraTS-PED-00223-000',
        'BraTS-PED-00326-000',
        'BraTS-PED-00330-000',
        'BraTS-PED-00348-000',
        'BraTS-PED-00351-000',
    ]]
    order_list = ["-t1c.nii.gz", "-t2f.nii.gz", "-t1n.nii.gz", "-t2w.nii.gz"]
    example_list_segmented = [
        [os.path.join(path, f"{Path(path).name}{ending}") for ending in order_list]
        for path in generate_examples_segmented
    ]
    
    gr.Examples(
        examples=example_list_segmented,
        inputs=[image_t1c, image_t2f, image_t1n, image_t2w],
        outputs=[mask_file, out_text],
        fn=main_func,
        cache_examples=False,
        label="Preloaded BraTS2024 Examples",
    )

    # Button Click Event
    btn.click(
        fn=main_func,
        inputs=[image_t1c, image_t2f, image_t1n, image_t2w],
        outputs=[mask_file, out_text],
    )

    # Dropdown Selection Events
    file_to_render.select(
        render_axial,
        inputs=[file_to_render, state_axial],
        outputs=[myimage_axial],
    )
    file_to_render.select(
        render_coronal,
        inputs=[file_to_render, state_coronal],
        outputs=[myimage_coronal],
    )
    file_to_render.select(
        render_sagittal,
        inputs=[file_to_render, state_sagittal],
        outputs=[myimage_sagittal],
    )

    # Slider Change Events
    slider_axial.change(
        render_axial,
        inputs=[file_to_render, slider_axial],
        outputs=[myimage_axial],
        api_name="axial_slider",
    )
    slider_coronal.change(
        render_coronal,
        inputs=[file_to_render, slider_coronal],
        outputs=[myimage_coronal],
        api_name="coronal_slider",
    )
    slider_sagittal.change(
        render_sagittal,
        inputs=[file_to_render, slider_sagittal],
        outputs=[myimage_sagittal],
        api_name="sagittal_slider",
    )

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860, show_api=False, favicon_path='./app_assets/favicon.ico', share=True)
