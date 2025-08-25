---
layout: default
---

**I have read the instructions and agree with the terms.** [Return to the application](https://nf1.hope4kids.io/).

The **CAVS-NF1: Central AI-enabled Volumetric Service for NF1** is a free, open-source web-based application designed at [Children's National Hospital](https://www.childrensnational.org/) 
for the segmentation and analysis of optic pathway gliomas associated with neurofibromatosis type 1 (NF1-OPG)  in  T1 magnetic resonance imaging (MRI). Developed in Python, this web tool aims to provide precise quantitative analysis of pediatric brain MRI, to support clinical decision-making in diagnosis and prognosis.  

With its user-friendly interface, **CAVS-NF1** provides automated segmentation and volumetric measurements within 2 minutes after uploading the t1 MRI sequences. This software offers **state-of-the-art performance** powered by our benchmarked segmentation model.  

# Usage

This software requires T1 MRI sequences: native pre-contrast T1-weighted (t1n) or 
contrast-enhanced T1-weighted (t1c). The MRI sequences should be 
uploaded in NIfTI format (*i.e.*, **.nii.gz**). Before uploading, 
we strongly recommend performing **de-identification** to remove any protected 
health information, including **defacing** if necessary. 

<!-- **Pre-processing** in the Segmenter is under development. At this time, 
we expect users to follow the standardized ["BraTS Pipeline"](https://arxiv.org/pdf/2404.15009) 
pre-processing, which includes co-registration of four sequences, and resampling to isotropic 1 mm resolution.  
Public tools such as the Cancer Imaging Phenomics Toolkit ([CaPTk](https://github.com/CBICA/CaPTk)) 
and Federated Tumor Segmentation ([FeTS](https://fets-ai.github.io/Front-End/process_data)) 
toolkits can be used for this purpose.   -->

Once the MRI sequences are uploaded, simply click check the box and push the **Start Segmentation** button to generate segmentation and volumetric measurements in the **Status** box. The process typically takes around 1 minute. Afterward, you can visualize both the image and the segmentation in axial, coronal, and sagittal views using the interactive **Sliders**. Segmentation results can be downloaded in NIfTI format by clicking the **Download Segmentation File** button.  

For **demonstration** purposes, we provide sample cases at the bottom of the page. 
Select one and click the **Start Segmentation** button to see how the software works.  

<!--# Source Code

The current version of the software is![v1.0](https://img.shields.io/badge/v1.0-brightgreen) 
and the source code is publicly available on GitHub 
([code](https://github.com/Precision-Medical-Imaging-Group/HOPE-Segmenter-Kids)) 
under license [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). -->

The software is developed and maintained by the [Precision Medical Imaging](https://research.childrensnational.org/labs/precision-medical) lab
at Children’s National Hospital in Washington, DC, USA.  

**Copyright Notification**  Copyright 2025 Children's National Medical Center.

# Contributors

This web app was made possible due to the efforts made by

[Abhijeet Parida](https://www.linkedin.com/in/a-parida/), [Zhifan Jiang](https://www.linkedin.com/in/zhifan-jiang-19917531/), [Syed Muhammad Anwar](https://www.linkedin.com/in/syed-anwar-5473b81a/), [Marius George Linguraru](https://www.linkedin.com/in/mglinguraru/)

# Citations

If you use and/or refer to this software in your research, please cite the following papers: 

* Jiang, Z., Parida, A., Anwar, S.M., Tang, Y., Roth, H.R., Fisher, M.J., Packer, R.J., Avery, R.A. and Linguraru, M.G., 2023, July. "Automatic Visual Acuity Loss Prediction in Children with Optic Pathway Gliomas using Magnetic Resonance Imaging". In *2023 45th Annual International Conference of the IEEE Engineering in Medicine & Biology Society (EMBC)*, Sydney, Australia (pp. 1-5). doi: [10.1109/EMBC40787.2023.10339961](https://ieeexplore.ieee.org/abstract/document/10339961)
* Avery, R.A., Mansoor, A., Liu, G.T., Trimboli− Heidler, C., Ying, G.S., Centrella, C.R., Eltoukhy, N., Packer, R.J., Fisher, M.J. and Linguraru, M.G., 2023. Larger tumor volume is associated with visual acuity loss and axonal degeneration in children with optic pathway gliomas secondary to neurofibromatosis type 1. *Neuro-Oncology Advances, 5(1)*, p.vdad107. doi:[10.1093/noajnl/vdad107](https://doi.org/10.1093/noajnl/vdad107)
* Avery, R.A., Mansoor, A., Idrees, R., Trimboli-Heidler, C., Ishikawa, H., Packer, R.J. and Linguraru, M.G., 2016. Optic pathway glioma volume predicts retinal axon degeneration in neurofibromatosis type 1. *Neurology, 87(23)*, pp.2403-2407. doi:[10.1212/WNL.000000000000340](https://doi.org/10.1212/WNL.000000000000340)

# Disclaimer

* This software is provided without any warranties or liabilities and is intended for research purposes only. 
It has not been reviewed or approved for clinical use by the Food and Drug Administration (FDA) or any other federal or state agency. 

* This software does not store any information uploaded to the platform. 
All uploaded and generated data are automatically deleted once the webpage is closed. 

# Contact

* New features are continually being developed. To stay informed about updates, 
report issues or provide feedback, please fill out the 
**online form** [here](https://forms.gle/kjMni6tpN1whA4RNA) or contact **Abhijeet Parida** [support@hope4kids.io](mailto:support@hope4kids.io) .   

* For more information, collaboration, or to receive the model in a Docker container 
for testing on large datasets locally, please contact 
**Prof. Marius George Linguraru** [contact@hope4kids.io](mailto:contact@hope4kids.io) with details on your intended use. 

**I have read the instructions and agree with the terms.** [Return to the application](https://nf1.hope4kids.io/).
