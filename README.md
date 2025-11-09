# Early Detection of Sepsis in Neonates Using Thermal Imaging

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-green.svg)](https://opencv.org/)

An AI-powered system for early detection of neonatal sepsis through automated thermal and visible spectrum image analysis in Neonatal Intensive Care Units (NICUs).

This project develops a non-invasive, real-time monitoring system that uses thermal imaging and artificial intelligence to detect early signs of neonatal sepsis. By analyzing temperature distribution patterns between central and peripheral body regions, the system aims to identify sepsis indicators before clinical symptoms appear.

*Neonate images won't be shown in this readme.* *For a detailed report access **'docs/Report.pdf'** file*

![Pipeline Overview](/docs/images/pipeline.png)
*System architecture: From dual-modality capture to clinical alert generation*

## The Problem

Neonatal sepsis kills approximately **17.6%** of affected newborns globally, with ~2,824 cases per 100,000 live births. Current diagnostic methods face critical limitations:

- **Delayed diagnosis**: Blood cultures require 24-48 hours while the "golden hour" for treatment is within 60 minutes
- **Invasive procedures**: Repeated blood draws harm fragile preterm infants
- **Non-specific symptoms**: Early sepsis mimics other conditions, making clinical assessment unreliable

This project addresses these challenges through continuous, non-invasive thermal monitoring powered by computer vision and deep learning.

## Our Solution

We developed a multi-stage AI pipeline that analyzes thermal and visible spectrum images to detect sepsis-indicative temperature patterns:

**Core Innovation**: Detecting temperature centralization (warm core + cold peripheries) that precedes clinical symptoms by monitoring the gradient between central body zones and extremities.

### System Pipeline

```
Thermal + RGB Images → Modality Alignment → Pose Detection → Quality Control → 
Temperature Analysis → Temporal Pattern Recognition → Clinical Alert
```

## Technical Architecture

### 1. Modality Alignment
Thermal (640×480) and RGB (3264×2448) images have different resolutions, zoom levels, and viewing angles. We need to match them so pose detection can work effectively. As pose can't be detected well in thermal images and temperature cannot be read in visible ones.

Solution: 
- Homography transformation using point-based correspondence
- Manual landmark selection (corners, joints, silhouette)
- Sub-pixel accuracy through bilinear interpolation
- Temporal synchronization within 2-second windows


### 2. Pose Detection with HRNet
Uses HRNet-W48 adapted for neonatal anatomy to detect 17 anatomical keypoints with 0.7 confidence threshold.

Temperature zones identified:
- Zone 1 (Core): Head, chest, shoulders
- Zone 2: Arms and legs  
- Zone 3 (Peripheral): Hands and feet (mapped from wrists/ankles)
  
The pre-trained model was originally designed for adults but successfully adapted to detect neonatal proportions.

![Zone Detection](/docs/images/zones.png)

### 3. Quality Control & Rejection
Ensures measurement reliability through:
- Anatomical completeness verification (minimum 1 Zone 1 + 1 Zone 3 point)
- Temperature range validation (28-42°C physiological bounds)
- Occlusion detection (tubes, bandages, sensors)
- Positioning assessment

### 4. Temperature Analysis
Gaussian-weighted averaging (15×15 kernel, σ=5) is applied across body zones to extract regional temperatures.

Sepsis indicators:
- Core-peripheral gradient >3.5°C
- Core temperature >38.5°C
- Sustained abnormal patterns over consecutive measurements

### 5. Temporal Pattern Recognition
Time-series tracking of Zone 1 vs Zone 3 temperatures with baseline establishment using median values. Alerts trigger when abnormal gradients persist for 5 or more consecutive readings.

## Results & Validation

Tested on 71 neonates from General University Hospital of Patras (Greece), with detailed analysis of 3 sepsis + fever cases:

| Case | Outcome | Key Finding |
|------|---------|-------------|
| Case 48 | Success | Perfect alignment with nurse-detected fever timing |
| Case 36 | Missed detection | Pose detection failure due to extreme positioning |
| Case 47 | False positive | Bandage color similarity caused measurement artifact |

### Performance Analysis

The system demonstrated accurate detection under ideal conditions (Case 48), where model detection perfectly aligned with nurse-documented fever onset. This validates the approach of using inter-zone temperature differentials.

However, significant limitations were identified:
- Sensitivity to medical equipment interference (bandages, tubes, sensors)
- Pose detection challenges in non-standard infant positions
- Requires high-quality, unobstructed thermal images

Case 36 showed how pose detection failures can result in complete missed detection, while Case 47 revealed how bandage color interference can create false patterns that mimic sepsis indicators. Case 48 optimal results appreciated in the following image:

![Results Visualization](/docs/images/resultsCase48.png)

## Technical Requirements
- Python 3.8+
- PyTorch (deep learning framework)
- OpenCV (image processing)
- PIL (image manipulation)
- HRNet-W48 (pose estimation)

**Key Dependencies**:
```bash
torch>=2.0.0
opencv-python>=4.5.0
numpy>=1.21.0
pillow>=9.0.0
```

**Hardware Requirements**:
- Thermal camera (PNG output, 640×480 resolution)
- RGB camera (3264×2448 resolution)
- CUDA-capable GPU (recommended for real-time processing)
- ~252GB storage for dataset


### Usage

As this work is for research purposes only and deals with sensitive data non-authorized for sharing the usage tab is empty.


## Future Enhancements

### Near-Term Improvements
- Automated alignment to replace manual point selection with feature matching algorithms
- Fine-tuned pose model trained specifically on neonatal dataset for better keypoint accuracy
- Enhanced artifact detection to improve bandage/equipment recognition and reduce false positives

### Long-Term Development
- LSTM temporal modeling for advanced time-series pattern prediction
- Multi-center validation across diverse NICU environments and patient populations
- Real-time dashboard with WebSocket-based clinical monitoring interface and risk scoring
- Regulatory approval pathway for EU MDR certification as Class IIb medical device

## Clinical Impact

Potential benefits:
- Reduces diagnostic delay from 24-48 hours to real-time detection
- Eliminates invasive blood draws for initial screening
- Enables earlier antibiotic administration within the critical "golden hour"
- Decreases sepsis-related mortality and long-term neurodevelopmental impairments

Target users: NICU clinicians at hospitals managing high-risk neonates, particularly preterm infants.

## Ethical & Regulatory Considerations

EU AI Act classification: High-risk AI system (Annexe III, Section 5a)

Compliance framework:
- GDPR and European Health Data Space (EHDS) adherence
- Human-in-the-loop design: final diagnosis remains with clinicians
- Explainable AI: confidence scores and visual explanations accompany alerts
- Continuous bias monitoring across ethnic and clinical subgroups

Safety mechanisms:
- Fail-safe operation with automatic fallback during system failures
- AES-256 encryption for data at rest
- Role-based access control with JWT authentication
- Comprehensive audit trails with cryptographic hashing

## Team

Marino Oliveros, Álvaro Sáenz-Torre, Luis Domene, Joan Bayona, Alejandra Reinares, Andreu Gascón

**Clinical partners:** General University Hospital of Patras, Greece & Department of Paedriatics, University of Patras
Universitat Autònoma de Barcelona

![partners](/docs/images/partners.png)


## Key References

- Shane, A. L., et al. (2017). *Neonatal sepsis*. The Lancet, 390(10104), 1770-1780.
- Sun, K., et al. (2019). *Deep high-resolution representation learning for human pose estimation*. arXiv:1902.09212.
- Ring, E. F. J., & Ammer, K. (2012). *Infrared thermal imaging in medicine*. Physiological Measurement, 33(3), R33-R46.
- Masino, A. J., et al. (2019). *Machine learning models for early sepsis recognition in the NICU*. PLoS One, 14(2), e0212665.

## License

This project is developed for research and educational purposes. Clinical deployment requires regulatory approval and additional validation studies.

*This work represents a proof-of-concept clinical decision support system. It is not intended for diagnostic use without clinical oversight and regulatory approval.*
