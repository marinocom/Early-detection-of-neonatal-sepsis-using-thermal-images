posture_detecition_pipeline Notebook:

	1. posture_detecition_pipeline first navigates thorugh the aligned images folder after modality alignment
	2. then it loads HRNET W48 and processes images storing keypoints in a json file for future processing.
	3. The Json will be saved in the full_output filder and the file will contain the following for each image:
		- Thermal Image Path
		- Aligned Image Path
		- Keypoints from the image with this attributes [x-coordinate, y-coordinate, part of the body, confidence]
			*if the desired keypoint doesn't exists with the provided threshold attributes are null/ no class:


	Sample of the output JSON:							
							{
       	"thermal_image": "29\\15.08.24\\HM20240815060955.jpeg",
        "aligned_image": "29\\15.08.24\\aligned_HM20240815060955_VIS.jpeg",
        "anotaciones": [
            {
                "x": 223,
                "y": 130,
                "class": "Zona1",
                "confidence": 0.7917551398277283
            },
            {
                "x": 353,
                "y": 200,
                "class": "codo_izq",
                "confidence": 0.9522820115089417
            },
            {
                "x": null,
                "y": null,
                "class": "no_present",
                "confidence": null
            },



* If we want to use the GPU from the cluster (very recommended) we will simply launch hrnet.slm into the terminal.

__ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __

HOW TO SETUP HRNET:

The best way to setup HRNET is following the official GitHub steps: https://github.com/HRNet/HRNet-Human-Pose-Estimation

Since the implementation is quite old (2019) it is required to create an environment using python = 3.6 and installing the requirement.txt file from this folder to the environment. Do this step before starting with Quick Start in the original GitHub README.

We are using the folling weights: pose_hrnet_w48_384x288.pth. Make sure you download the correct weights and yaml file (configuration file) from the original google drive.

*we must change the environment name in the slurm file if we want to use the GPU.



