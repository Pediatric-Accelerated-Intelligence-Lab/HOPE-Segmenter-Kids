from enum import Enum
# python 3.11 only supports StrEnum natively
# so we define our own for compatibility with 3.8+
class StrEnum(str, Enum):
    pass

class RegionName(StrEnum):
    NETC = "NON-ENHANCING TUMOR CORE (NETC)"
    ET = "ENHANCING TUMOR (ET)"
    CC = "CYSTIC COMPONENT (CC)"
    NET = "NON-ENHANCING TUMOR (NET)"
    ED = "EDEMA (ED)"
    GTV = "GROSS TUMOR VOLUME (GTV)"
    SNFH = "SURROUNDING NON-ENHANCING FLAIR HYPERINTENSITY (SNFH)"
    RC = "RESECTION CAVITY (RC)"

class TaskName(StrEnum):
    gli = "Task 1 - BraTS-GLI"
    men = "Task 2 - BraTS-MEN"
    #menrt = "Task 3 - BraTS-MEN-RT"
    met = "Task 4 - BraTS-MET"
    ssa = "Task 5 - BraTS-SSA"
    peds = "Task 6 - BraTS-PED"


DUMMY_DIR = "BraTS-PED-00019-000"
DUMMY_FILE_NAMES = {modality: f"{DUMMY_DIR}-{modality}.nii.gz" for modality in ["t1c", "t2f", "t1n", "t2w"]}
DOCKER_TASK_DICT = {task.value: f"aparida12/brats2025:{task.name}" for task in TaskName}

TASK_NAME_MAPING ={
    TaskName.peds.value: "Pediatric Tumor Segmentation",
    TaskName.gli.value: "Adult Glioma Segmentation",
    TaskName.ssa.value: "Sub-Saharan Africa Adult Glioma Segmentation",
    #TaskName.menrt.value: "menrt",
    TaskName.met.value: "Adult Metastasis Segmentation",
    TaskName.men.value: "Adult Pre-treatment Meningioma Segmentation",
}
LABEL_MAPPING_FACTORY = {
    TaskName.peds.value: {
        1: RegionName.ET.value,
        2: RegionName.NET.value,
        3: RegionName.CC.value,
        4: RegionName.ED.value
    },
    TaskName.gli.value: {
        1: RegionName.NETC.value,
        2: RegionName.SNFH.value,
        3: RegionName.ET.value,
        4: RegionName.RC.value
    },
    TaskName.ssa.value: {
        1: RegionName.NETC.value,
        2: RegionName.ED.value,
        3: RegionName.ET.value
    },
    # TaskName.menrt.value: {
    #     1: RegionName.GTV.value
    # },
    TaskName.met.value: {
        1: RegionName.NETC.value,
        2: RegionName.SNFH.value,
        3: RegionName.ET.value,
        4: RegionName.RC.value
    },
    TaskName.men.value: {
        1: RegionName.NETC.value,
        2: RegionName.SNFH.value,
        3: RegionName.ET.value,
    }
}

SUFFIX = {
        "T2 FLAIR": "t2f",
        "native T1": "t1n",
        "post-contrast T1-weighted": "t1c",
        "T2 weighted": "t2w",
    }

AXIS_MAP = {"axial": 0, "coronal": 1, "sagittal": 2}
EXAMPLE_LIST = ['BraTS-GLI-00492-000', 'BraTS-MEN-00134-000', 'BraTS-MET-00910-000', 'BraTS-PED-00019-000', 'BraTS-SSA-00163-000' ]
EXAMPLE_TASKS = [TaskName.gli.value, TaskName.men.value, TaskName.met.value, TaskName.peds.value, TaskName.ssa.value]
EXAMPLE_OUTPUTS = {folder: f'example_outs/{folder}.nii.gz' for folder in EXAMPLE_LIST}