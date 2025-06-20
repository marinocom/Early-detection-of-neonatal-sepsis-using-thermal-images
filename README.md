# **Early Detection of Sepsis in Neonates using Thermal Imaging**

An AI-powered system for early detection of neonatal sepsis through automated thermal and visible spectrum image analysis in Neonatal Intensive Care Units (NICUs).

## Project Overview

This project develops a non-invasive, real-time monitoring system that uses thermal imaging and artificial intelligence to detect early signs of neonatal sepsis. By analyzing temperature distribution patterns between central and peripheral body regions, the system aims to identify sepsis indicators before clinical symptoms appear.

### Key Features
- **Modality Alignment/Cropping mechanisms**: Processes both thermal (640x480) and visible spectrum (3264x2448) images
- **Pose detection**: Uses HRNet to identify 17 anatomical keypoints on neonates
- **Temperature analysis**: Monitors core-to-peripheral temperature differentials
- **Time series & Alarm raising**: Triggers warnings when sepsis-indicative patterns are detected

## Getting Started

### Prerequisites
- Python 3.8+ (except for Pose Detection -> See README inside the folder)
- CUDA-capable GPU (recommended for real-time processing)
- Thermal camera with PNG output capability
- RGB camera for visible spectrum imaging
