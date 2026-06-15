# Standard library
import os
import glob
import shutil
import logging
import subprocess
import time
from pathlib import Path
from typing import Tuple, List, Dict, Any

# Third-party libraries
import numpy as np
import nibabel as nib
import PIL
import gradio as gr

# Local modules
from fops import delete_make_folder, get_img_mask, render_slice
from app_assets.utils import image_to_base64
from constants import (
    DUMMY_DIR, DUMMY_FILE_NAMES, DOCKER_TASK_DICT, LABEL_MAPPING_FACTORY,
    SUFFIX, AXIS_MAP, TASK_NAME_MAPING, EXAMPLE_LIST, EXAMPLE_TASKS, EXAMPLE_OUTPUTS
)
# Example usage
image_path = "./app_assets/app_header.png"
logo = image_to_base64(image_path)

# Configure the logger for the module
logger = logging.getLogger(__file__)

# Dictionary to store intermediate results and paths
mydict: Dict[str, Any] = {}


def run_inference(
    image_t1c: Path, image_t2f: Path, image_t1n: Path, image_t2w: Path, docker: str
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
    # remove old cache files 
    # Define and create the input directory
    global mydict
    mydict = {}

    # Aggregate image paths into a dictionary
    image_paths = {"t1c": image_t1c, "t2f": image_t2f, "t1n": image_t1n, "t2w": image_t2w}

    # Setup input directory
    input_path = Path("/tmp/brats2025-app") / DUMMY_DIR
    delete_make_folder(input_path)
    
    # Setup output directory (delete and recreate)
    output_folder = Path("./segmenter/mlcube/outs")
    delete_make_folder(output_folder)

    # Define paths for the output segmentation
    output_path = output_folder / f"seg_{image_t1c.name}"
    fake_output_path = output_folder / f"{DUMMY_DIR}.nii.gz"

    # Copy images to input directory using dummy filenames
    for key, file in image_paths.items():
        shutil.copy(file, input_path / DUMMY_FILE_NAMES[key])

    real_name = str(image_t1c.name).replace("-t1c.nii.gz", "")
    if not (real_name in EXAMPLE_OUTPUTS.keys()):
        # Build and run Docker command
        mlcube_cmd = (
            f"docker run --rm --network none --gpus=all --memory=16G --shm-size 4G "
            f"-v {input_path.parent}:/input/:ro -v {output_folder.absolute()}:/output/:rw "
            f"{DOCKER_TASK_DICT[docker]}"
        )
        print(mlcube_cmd)

        # Execute the Docker command
        subprocess.run(mlcube_cmd, shell=True, check=True)
        subprocess.run("docker system prune -f", shell=True, check=True)

        # Move the fake output to the actual output path
        os.rename(fake_output_path, output_path)
    else:
        # search closest match in EXAMPLE OUTPUTS
        fake_output_path = EXAMPLE_OUTPUTS[real_name]
        # randomly wait for 60-75 seconds to simulate processing time
        wait_time = np.random.randint(60, 75)
        
        time.sleep(wait_time)
        # copy the example output to the output path
        shutil.copy(fake_output_path, output_path)
    return str(input_path), str(output_path)


def main_func(
    image_t1c: Path, image_t2f: Path, image_t1n: Path, image_t2w: Path, model_docker: str
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
    global mydict

    # Run inference and get paths
    input_path, mask_path = run_inference(
        Path(image_t1c), Path(image_t2f), Path(image_t1n), Path(image_t2w), model_docker
    )

    # Retrieve all NIfTI files in the input directory
    image_files = glob.glob(os.path.join(input_path, "*.nii.gz"))
    mydict.update({"img_path": image_files, "mask_path": mask_path})

    # Get image and mask data
    images = [get_img_mask(f, mask_path, logger)[0] for f in image_files]
    _, img_obj, mask = get_img_mask(image_files[0], mask_path, logger)

    # Store image and mask for display
    mydict.update({"img": images[0], "mask": mask, 
                   "t1c": images[0], "t2f": images[1], "t1n": images[2], "t2w": images[3]})

    spacing = img_obj.GetSpacing()

    # Calculate the multiplier for volume calculation
    multiplier_ml = 0.001 * np.prod(spacing)


    # Compute volumetrics
    unique, counts = np.unique(mask, return_counts=True)
    total_vol = 0
    vol_str = ""
    for lbl, count in zip(unique, counts):
        vol = multiplier_ml * count
        mydict[f"vol_lbl{int(lbl)}"] = vol
        if lbl != 0:
            total_vol += vol
            vol_str += f"{LABEL_MAPPING_FACTORY[model_docker][int(lbl)]} {vol:.3f} ml;\n"
    mydict["vol_total"] = total_vol

    status_message = (
        f"{TASK_NAME_MAPING[model_docker]} done!\n"
        f"Total tumor volume segmented {total_vol:.3f} ml;\n\n"
        f"{vol_str}"
    )

    return mask_path, status_message


def render(file_to_render: str, x: int, view: str, model_docker) -> Tuple[PIL.Image.Image, List[Tuple[np.ndarray, str]]]:
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
    if "img_path" not in mydict:
        # Return an empty image and no annotations if paths are not available
        return PIL.Image.fromarray(np.zeros((10, 10), dtype=np.uint8)), []

    # Retrieve image and mask data
    img, mask = mydict[SUFFIX[file_to_render]], mydict["mask"]

    axis = AXIS_MAP.get(view, 0)

    # Ensure the slice index is within valid range
    x = np.clip(x, 0, img.shape[axis] - 1)

    # Render the specific slice
    slice_img, slice_mask = render_slice(img, mask, x, view, model_docker)
    

    # Convert to PIL image
    im = PIL.Image.fromarray(slice_img.astype(np.uint8))

    # Generate annotations
    annotations = [
        (slice_mask == lbl,
         f"{LABEL_MAPPING_FACTORY[model_docker][int(lbl)].split('(')[-1][:-1]}: "
         f"{mydict.get(f'vol_lbl{int(lbl)}', 0):.3f} ml")
        for lbl in np.unique(mask)[1:]  # Skip background label 0
    ]

    return im, annotations



def update_slider_limits(mask_file):
    img_data = mydict.get("mask", None)
    if img_data is None:
        return gr.update(), gr.update(), gr.update()  # No file uploaded yet
    axial_axis = 0
    coronal_axis = 1
    sagittal_axis = 2

     # Get the dimensions of the mask
    max_axial, max_coronal, max_sagittal = (img_data.shape[ax] - 1 for ax in [axial_axis, coronal_axis, sagittal_axis])  # Axial slices
    def median_nonempty_slice(mask, slice_axis):
        reduce_axes = tuple(ax for ax in range(mask.ndim) if ax != slice_axis)
        nonempty_slices = mask.any(axis=reduce_axes)
        indices = np.flatnonzero(nonempty_slices)

        if indices.size == 0:
            return 0

        return int(np.median(indices))

    median_axial = median_nonempty_slice(img_data, axial_axis)
    median_coronal = median_nonempty_slice(img_data, coronal_axis)
    median_sagittal = median_nonempty_slice(img_data, sagittal_axis)

    return gr.update(maximum=max_axial, value=median_axial), gr.update(maximum=max_coronal, value=median_coronal), gr.update(maximum=max_sagittal, value=median_sagittal)


def render_view(file_to_render: str, x: int, model_docker: str, view: str) -> Tuple[PIL.Image.Image, List[Tuple[np.ndarray, str]]]:
    """Render a slice of the image for the given view ('axial', 'coronal', 'sagittal')."""
    return render(file_to_render, x, view, model_docker)

# Gradio UI Setup
with gr.Blocks(title="Brain Tumor Segmenter") as demo:
    # Header
    gr.HTML(
        value=f"<center><font size='6'><bold> Children's National Brain Tumor Segmenter</bold></font></center>"
        f"<p style='margin-top: 1rem; margin-bottom: 1rem'> <img src='{logo}' alt='Childrens National Logo' style='display: inline-block'/></p>"
        f"<center><font size='4'> Welcome to the cluster of brain tumor segmenter. Partial support for this work is provided by the NIH- National Cancer Institute grant UG3-UH3 CA236536. </font></center>"
    )

    with gr.Row():
        gr.Column(scale=1)   # left spacer
        with gr.Column(scale=1):
            enable_checkbox = gr.Checkbox(
                label="I have read the instructions and accept the terms and conditions.", 
                value=False, 
                info="<span style='font-size: 1.5em;'>Please read the [instructions](https://docs.hope4kids.io/HOPE-Segmenter-Kids/) before using the app.</span>", 
                container=False)
        gr.Column(scale=1)

    # Dropdown for Model Selection
    with gr.Row():
        gr.Column(scale=1)   # left spacer
        with gr.Column(scale=1):
            dropdown_model = list(DOCKER_TASK_DICT.keys())
            model_docker = gr.Dropdown(
                dropdown_model,
                value =  dropdown_model[0],
                label='Choose the inference engine for the segmentation'
            )
        gr.Column(scale=1) 
        

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

    with gr.Row(equal_height=True):
        gr.Column(scale=2)   # left spacer
        with gr.Column(scale=1):
            btn = gr.Button("Start Segmentation", interactive=False)
        gr.Column(scale=2) 

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
        gr.Column(scale=1)   # left spacer
        with gr.Column(scale=1):
            dropdown_modality = ["T2 FLAIR","native T1", "post-contrast T1-weighted", "T2 weighted"]
            file_to_render = gr.Dropdown(
                dropdown_modality,
                value =  dropdown_modality[0],
                label='Choose the scan to overlay the segmentation on'
            )
        gr.Column(scale=1) 
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
        
        slider_coronal = gr.Slider(
            0, 155, step=1, label="Coronal Slice", info="Adjust the coronal slice."
        )  # Max val needs to be updated by user.
        
        slider_sagittal = gr.Slider(
            0, 155, step=1, label="Sagittal Slice", info="Adjust the sagittal slice."
        )  # Max val needs to be updated by user.
        

    # Segmentation File Download
    with gr.Row():
        mask_file = gr.File(label="Download Segmentation File", height="vw")

    mask_file.change(
    update_slider_limits,
    inputs=[mask_file],
    outputs=[slider_axial, slider_coronal, slider_sagittal]
    )

    #Examples Setup
    example_dir = "./examples"
    generate_examples =  [os.path.join(example_dir, names) for names in EXAMPLE_LIST]
    order_list = ["-t1c.nii.gz", "-t2f.nii.gz", "-t1n.nii.gz", "-t2w.nii.gz"]
    example_list = [
        [os.path.join(path, f"{Path(path).name}{ending}") for ending in order_list]
        for path in generate_examples
    ]
    full_example_list = [ [task] + example  for example, task in zip(example_list, EXAMPLE_TASKS)]

    gr.Examples(
        examples=full_example_list,
        inputs=[model_docker, image_t1c, image_t2f, image_t1n, image_t2w],
        outputs=[mask_file, out_text],
        fn=main_func,
        cache_examples=False,
        label="Preloaded Examples",
    )

    # Button Click Event
    btn.click(
        fn=main_func,
        inputs=[image_t1c, image_t2f, image_t1n, image_t2w, model_docker],
        outputs=[mask_file, out_text],
    )

    # Dropdown Selection Events
    file_to_render.select(
    lambda f, x, m: render_view(f, x, m, "axial"),
    inputs=[file_to_render, slider_axial, model_docker],
    outputs=[myimage_axial],
    )

    file_to_render.select(
        lambda f, x, m: render_view(f, x, m, "coronal"),
        inputs=[file_to_render, slider_coronal, model_docker],
        outputs=[myimage_coronal],
    )

    file_to_render.select(
        lambda f, x, m: render_view(f, x, m, "sagittal"),
        inputs=[file_to_render, slider_sagittal, model_docker],
        outputs=[myimage_sagittal],
    )

    # Slider Change Events
    slider_axial.change(
    lambda f, x, m: render_view(f, x, m, "axial"),
    inputs=[file_to_render, slider_axial, model_docker],
    outputs=[myimage_axial],
    api_name="axial_slider",
    )
    slider_coronal.change(
        lambda f, x, m: render_view(f, x, m, "coronal"),
        inputs=[file_to_render, slider_coronal, model_docker],
        outputs=[myimage_coronal],
        api_name="coronal_slider",
    )
    slider_sagittal.change(
        lambda f, x, m: render_view(f, x, m, "sagittal"),
        inputs=[file_to_render, slider_sagittal, model_docker],
        outputs=[myimage_sagittal],
        api_name="sagittal_slider",
    )
    demo.css = "footer {display: none !important;}"
    gr.Markdown("<center>Built with ❤️ at <a href='https://www.childrensnational.org/'>Children's National</a></center>")


if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860, show_api=False, favicon_path='./app_assets/favicon.ico')
