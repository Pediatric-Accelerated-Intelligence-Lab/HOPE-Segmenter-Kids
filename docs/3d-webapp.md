# 3D-Medical-Segmentation-Viewer: A step-by-step guide to deploying a browser-based 3D medical segmentation application

*Ananya Vivek, Abhijeet Parida, Marius George Linguraru, and Syed Muhammad Anwar*

---

## Introduction

The manual segmentation of MRI scans is a time-intensive task. This web app is designed to facilitate clinicians in identifying tumor growth and volume. For example, the standard brain MRI for a glioma patient requires multiple sequences: T1-Weighted, T2-Weighted, FLAIR, and T1 Contrast-Enhanced. Then, a clinician must scroll through every axial, sagittal, and coronal slice to calculate the volume of the tumor. Users can run and review medical image segmentation models directly through a web browser. End users do not need to install the application, configure a development environment, or have access to a GPU. The application can be deployed in CPU-only environments, making it easier to share segmentation tools with researchers, clinicians, and collaborators.

Many researchers develop promising medical imaging algorithms but have limited opportunities to evaluate them using real clinical workflows and clinical data. This repository is intended to help researchers deploy their algorithms as accessible web applications so that clinicians can test the models, review their outputs, and provide practical feedback. The goal of this web application is for clinicians to upload their patients' MRI scans, select the corresponding tumor type, and receive interactive axial, sagittal, and coronal views of the segmentation along with volumetric measurements for each tumor subregion within minutes. 

This app is a segmentation app. You input multiple MRI scans, and the app outputs the full 3D segmentation mask and tumor volumes. The frontend is built using Gradio, an open-source Python library that allows for building interactive websites with machine learning models. Each Docker container contains an AI model that will perform the corresponding task. The backend is designed using Gradio and Docker, such that adding a new segmentation task only requires changes in constants.py. It also features parallel execution, allowing multiple models to run simultaneously. 

See an example of an app deployed using this repository at [https://segmenter.hope4kids.io](https://segmenter.hope4kids.io)


## Clone Repository

Before proceeding, you must have Python version 3.11 and Docker downloaded on your computer. To confirm you have the correct Python version installed, type `python --version` in your terminal. To confirm you have Docker installed, type `docker --version` in your terminal. 

To edit the codebase, you first clone the repository on your local device.

```bash
git clone https://github.com/Pediatric-Accelerated-Intelligence-Lab/3D-Medical-Segmentation-Viewer.git
```


Otherwise, you may download Visual Studio Code using a standard web browser. Then, navigate to the repository web page on your browser. Click on the green button that reads "Code" and copy the HTTPS link. Now, in VS Code, click "Clone Git Repository".

<img width="412" height="294" alt="VSCODE SideBar" src="https://github.com/user-attachments/assets/f94ffde5-6cb8-4d5e-b735-0805a8b13316" />

Copy the HTTPS link into the top search bar and press `Enter`. 

<img width="662" height="75" alt="VSCODE ENTER URL" src="https://github.com/user-attachments/assets/895266fb-a0f3-419d-b5ed-76c751ade834" />


## Add a Docker Container

Adding a Docker container requires a few steps in the `constants.py` file. 

Register the task name inside `class TaskName`. Follow the same pattern as the others: `newtask = "New Task Display Name"`

```python
class TaskName(StrEnum):
      gli = "Pre- and Post-Treatment Adult Glioma"
```
Inside `DOCKER_TASK_DICT`, add a line that points to a Docker image, which folder in the container holds the input scans, and whether the folder should be `"ro"` (read only) or `"rw"` (writable). 

example: `TaskName.newtask.value: ("yourdockerimage", "/input/", "ro")`

```python
DOCKER_TASK_DICT = {
    TaskName.gli.value:    ("aparida12/brats2025:gli", "/input/", "ro")
}
```

In `DOCKER_OUTPUT`, add a line that will indicate which folder the container writes its results into (`"output_dir"` or `"input_dir"`) and what the output file name looks like

example: `TaskName.newtask.value: ("output_dir", f"{DUMMY_DIR}.nii.gz")`

```python
DOCKER_OUTPUT = {
    TaskName.gli.value:   ("output_dir", f"{DUMMY_DIR}.nii.gz")
}
```

In `TASK_NAME_MAPPING`, add a line that gives a display name. This will be displayed in the dropdown menu in the app. 

Example: `TaskName.newtask.value: "New Task Display Name"`

```python
TASK_NAME_MAPPING = {
    TaskName.gli.value: "Adult Glioma Segmentation"
}
```

In `LABEL_MAPPING_FACTORY`, define what the colored regions are. Each number represents a label ID that the container outputs, and it is mapped to a region name from `RegionName`. If the region your container needs isn't listed, add it to `RegionName` first. 

```python
LABEL_MAPPING_FACTORY = {
    TaskName.gli.value: {
        1: RegionName.NETC.value,
        2: RegionName.SNFH.value,
        3: RegionName.ET.value,
        4: RegionName.RC.value
    }
}
```
Indicate which scan types your container needs. If it needs all four scan types (FLAIR, T1, T2, T1c) add it to `FULL_MODALITY_TASKS`. If it doesn't need all four, indicate which tasks it needs like this: 

`TASK_MODALITIES[TaskName.newtask.value] = ["native T1", "post-contrast T1-weighted"]`

In `DUMMY_FILE_NAMES`, indicate what the input filenames look like. 

```python
DUMMY_FILE_NAMES = {
    TaskName.gli.value:   ALL_TASKS,
}
```
See examples below for a detailed understanding:

### Integrating MEN-RT container (accepts one imaging modality)

**Step 1.** Register the task name inside `class TaskName`
```python
class TaskName(StrEnum):
      gli = "Pre- and Post-Treatment Adult Glioma"
      menrt = "Pre-Radiotherapy Meningioma (BraTS-MEN-RT)"
```
**Step 2.** Add the Docker image to `DOCKER_TASK_DICT`
```python
DOCKER_TASK_DICT = {
    TaskName.gli.value:    ("aparida12/brats2025:gli", "/input/", "ro"),
    TaskName.menrt.value: ("aparida12/brats2025:menrt", "/input/", "ro"),
}
```
**Step 3.** Add to `DOCKER_OUTPUT`
```python
DOCKER_OUTPUT = {
    TaskName.gli.value:   ("output_dir", f"{DUMMY_DIR}.nii.gz"),
    TaskName.menrt.value:   ("output_dir", f"{DUMMY_DIR}.nii.gz"),
}
```
**Step 4.** Add the display name to `TASK_NAME_MAPPING`
```python
TASK_NAME_MAPPING = {
    TaskName.gli.value: "Adult Glioma Segmentation",
    TaskName.menrt.value: "Meningioma Segmentation Pre-Radiotherapy"
}
```
**Step 5.** Add the required regions to `RegionName` and `LABEL_MAPPING_FACTORY`.
   
```python
class RegionName(StrEnum):
    NETC = "NON-ENHANCING TUMOR CORE (NETC)"
    ET = "ENHANCING TUMOR (ET)"
    SNFH = "SURROUNDING NON-ENHANCING FLAIR HYPERINTENSITY (SNFH)"
    GTV = "GROSS TUMOR VOLUME (GTV)"

```

```python
LABEL_MAPPING_FACTORY = {
    TaskName.gli.value: {
        1: RegionName.NETC.value,
        2: RegionName.SNFH.value,
        3: RegionName.ET.value,
        4: RegionName.RC.value
    },
    TaskName.menrt.value: {
         1: RegionName.GTV.value
     }
   }
```
**Step 6.** Indicate the scan types needed. This container requires only one.
   
```python
TASK_MODALITIES[TaskName.menrt.value] = ["post-contrast T1-weighted"]
```
**Step 7.** In `DUMMY_FILE_NAMES`, indicate what the input filenames look like.
```python
DUMMY_FILE_NAMES = {
    TaskName.gli.value:   ALL_TASKS,
    TaskName.menrt.value: {"t1c": f"{DUMMY_DIR}-t1c.nii.gz"}
}
```
**Integrating PEDS container (accepts 4 imaging modalities)**

**Step 1.** Register the task name inside `class TaskName`
```python
class TaskName(StrEnum):
      gli = "Pre- and Post-Treatment Adult Glioma"
      menrt = "Pre-Radiotherapy Meningioma (BraTS-MEN-RT)"
      peds = "Pre-Treatment Pediatric Glioma (BraTS-PED)"
```

**Step 2.** Add the docker image to `DOCKER_TASK_DICT`
```python
DOCKER_TASK_DICT = {
    TaskName.gli.value:    ("aparida12/brats2025:gli", "/input/", "ro"),
    TaskName.menrt.value: ("aparida12/brats2025:menrt", "/input/", "ro"),
    TaskName.peds.value:    ("aparida12/brats2025:peds", "/input/", "ro")
}
```
**Step 3.** Add to `DOCKER_OUTPUT`
```python
DOCKER_OUTPUT = {
    TaskName.gli.value:   ("output_dir", f"{DUMMY_DIR}.nii.gz"),
    TaskName.menrt.value:   ("output_dir", f"{DUMMY_DIR}.nii.gz"),
    TaskName.peds.value:  ("output_dir", f"{DUMMY_DIR}.nii.gz"),
}
```

**Step 4.** Add the display name to `TASK_NAME_MAPPING`
```python
TASK_NAME_MAPPING = {
    TaskName.gli.value: "Adult Glioma Segmentation",
    TaskName.menrt.value: "Meningioma Segmentation Pre-Radiotherapy",
    TaskName.peds.value: "Pediatric Tumor Segmentation"

}
```
**Step 5.** Add the required regions to `RegionName` and `LABEL_MAPPING_FACTORY`.
   
```python
class RegionName(StrEnum):
    NETC = "NON-ENHANCING TUMOR CORE (NETC)"
    ET = "ENHANCING TUMOR (ET)"
    SNFH = "SURROUNDING NON-ENHANCING FLAIR HYPERINTENSITY (SNFH)"
    GTV = "GROSS TUMOR VOLUME (GTV)"
    NET = "NON-ENHANCING TUMOR (NET)"
    ED = "EDEMA (ED)"
```

```python
LABEL_MAPPING_FACTORY = {
    TaskName.gli.value: {
        1: RegionName.NETC.value,
        2: RegionName.SNFH.value,
        3: RegionName.ET.value,
        4: RegionName.RC.value
    },
    TaskName.menrt.value: {
         1: RegionName.GTV.value
     },
    TaskName.peds.value: {
            1: RegionName.ET.value,
            2: RegionName.NET.value,
            3: RegionName.CC.value,
            4: RegionName.ED.value
     }
   }
```

**Step 6.** Indicate the scan types needed. This container requires all four, so it is added to `FULL_MODALITY_TASKS`
   
```python
FULL_MODALITY_TASKS = (
    TaskName.gli.value,
    TaskName.peds.value
```
**Step 7.** In `DUMMY_FILE_NAMES`, indicate what the input filenames look like.
```python
DUMMY_FILE_NAMES = {
    TaskName.gli.value:   ALL_TASKS,
    TaskName.menrt.value: {"t1c": f"{DUMMY_DIR}-t1c.nii.gz"},
    TaskName.peds.value:  ALL_TASKS,
}
```

## Deploy App
Once all the Docker containers are registered, simply deploy the app by running the command: 
```bash
bash deploy.sh
```

---
