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
    menrt = "Task 3 - BraTS-MEN-RT"
    met = "Task 4 - BraTS-MET"
    ssa = "Task 5 - BraTS-SSA"
    peds = "Task 6 - BraTS-PED"


DUMMY_DIR = "BraTS-PED-00019-000"
DUMMY_FILE_NAMES = {modality: f"{DUMMY_DIR}-{modality}.nii.gz" for modality in ["t1c", "t2f", "t1n", "t2w"]}
DOCKER_TASK_DICT = {task.value: f"aparida12/brats-{task.name}-2024:v20250123" for task in TaskName}

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
    TaskName.menrt.value: {
        1: RegionName.GTV.value
    },
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