import json
import matplotlib.pyplot as plt
import cv2
import os
from matplotlib.patches import Circle
import numpy as np
import datetime  
"""
This script provides visualization tools for annotated thermal and aligned RGB images of newborns.

Main features:
- Loads annotation data from a JSON file containing keypoints and metadata for each image pair.
- Visualizes thermal and aligned images side by side, overlaying annotated keypoints and temperature values.
- Allows browsing through filtered images within a user-specified time frame and for a specific baby ID (hardcoded as 35).
- Supports saving annotated images with keypoints and labels drawn on them.
- Enables navigation through images using left and right arrow keys in the visualization window.
- Includes robust error handling for missing files and incorrect timestamp formats.

Usage:
- Run the script and input the desired start and end times to filter images.
- Optionally choose to save annotated images.
- Use the arrow keys to browse through the filtered image set.

"""

BASE_PATH_ALIGNED=r"D:\newbornValMatrixAligned"
BASE_PATH_THERMAL=r"D:\newborn"
# Load the JSON data
with open("json/final_annotations_validation.json", "r") as file:
    data = json.load(file)

# Function to visualize a single pair of images with annotations
def visualize_image_pair(idx, save_annotated=True):
    entry = data[idx]
    thermal_path = os.path.join(BASE_PATH_THERMAL, entry["thermal_image"])
    aligned_path = os.path.join(BASE_PATH_ALIGNED, entry["aligned_image"])
    
    print(thermal_path)
    print(aligned_path)
    
    # Load images
    thermal_img = cv2.imread(thermal_path)
    aligned_img = cv2.imread(aligned_path)

    # Check if the images were loaded successfully
    if thermal_img is None:
        raise FileNotFoundError(f"Could not load thermal image: {thermal_path}")
    if aligned_img is None:
        raise FileNotFoundError(f"Could not load aligned image: {aligned_path}")

    # Create copies for annotation
    thermal_annotated = thermal_img.copy()
    aligned_annotated = aligned_img.copy()

    # Define colors for OpenCV (BGR format)
    opencv_colors = {
        "Zona1": (0, 0, 255),
        "codo_izq": (255, 0, 0),
        "codo_drc": (255, 255, 0),
        "rodilla_izq": (0, 255, 0),
        "rodilla_drc": (255, 0, 255),
        "mano_izq": (0, 255, 255),
        "mano_drc": (255, 255, 255),
        "pie_izq": (128, 0, 128),
        "pie_drc": (0, 165, 255)
    }

    for annot in entry["anotaciones"]:
        if annot["x"] is not None and annot["y"] is not None:
            x, y = annot["x"], annot["y"]
            class_name = annot["class"]
            label = f"{class_name}"
            if annot["temperature"] is not None:
                label += f"\n{annot['temperature']:.1f}°C"

            # Add OpenCV annotations to the thermal image
            cv2.circle(
                thermal_annotated,
                (int(x), int(y)),
                5,
                opencv_colors.get(class_name, (0, 0, 255)),
                -1
            )
            cv2.putText(
                thermal_annotated,
                label.replace("\n", " "),  # For readability in OpenCV
                (int(x + 10), int(y)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1
            )

            # Add OpenCV annotations to the aligned image
            cv2.circle(
                aligned_annotated,
                (int(x), int(y)),
                5,
                opencv_colors.get(class_name, (0, 0, 255)),
                -1
            )
            cv2.putText(
                aligned_annotated,
                label.replace("\n", " "),
                (int(x + 10), int(y)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1
            )

    if save_annotated:
        # Create a directory for saving annotated images
        save_dir = "saved_images"
        os.makedirs(save_dir, exist_ok=True)

        base_filename = os.path.splitext(os.path.basename(entry["thermal_image"]))[0]
        thermal_annot_path = os.path.join(save_dir, f"{base_filename}_thermal_annot.png")
        aligned_annot_path = os.path.join(save_dir, f"{base_filename}_aligned_annot.png")
        
        cv2.imwrite(thermal_annot_path, thermal_annotated)
        cv2.imwrite(aligned_annot_path, aligned_annotated)
        print(f"Saved annotated thermal image to: {thermal_annot_path}")
        print(f"Saved annotated aligned image to: {aligned_annot_path}")

    # Convert to RGB for display
    thermal_img = cv2.cvtColor(thermal_img, cv2.COLOR_BGR2RGB)
    aligned_img = cv2.cvtColor(aligned_img, cv2.COLOR_BGR2RGB)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Display images
    ax1.imshow(thermal_img)
    ax1.set_title('Thermal Image')
    ax1.axis('off')
    
    ax2.imshow(aligned_img)
    ax2.set_title('Aligned Image')
    ax2.axis('off')
    
    # Add points and labels to both images
    colors = {
        "Zona1": "red",
        "codo_izq": "blue",
        "codo_drc": "cyan",
        "rodilla_izq": "green",
        "rodilla_drc": "magenta",
        "mano_izq": "yellow",
        "mano_drc": "white",
        "pie_izq": "purple",
        "pie_drc": "orange"
    }
    
    for annot in entry["anotaciones"]:
        if annot["x"] is not None and annot["y"] is not None:
            x, y = annot["x"], annot["y"]
            class_name = annot["class"]
            color = colors.get(class_name, "red")
            
            # Create label text
            label = f"{class_name}"
            if annot["temperature"] is not None:
                label += f"\n{annot['temperature']:.1f}°C"
            
            # Add points and labels to thermal image
            ax1.add_patch(Circle((x, y), 5, color=color, alpha=0.7))
            ax1.text(x + 10, y, label, fontsize=9, color='white', 
                     bbox=dict(facecolor=color, alpha=0.7))
            
            # Add points and labels to aligned image
            ax2.add_patch(Circle((x, y), 5, color=color, alpha=0.7))
            ax2.text(x + 10, y, label, fontsize=9, color='white', 
                     bbox=dict(facecolor=color, alpha=0.7))
    
    plt.tight_layout()
    return fig

# Visualize the first image pair (index 0)
#fig = visualize_image_pair(0)
#plt.show()

# Add functionality to iterate through multiple images
def browse_images(data, indices, save_annotated=False):
    if not indices:
        print("No images found in the specified time frame.")
        return
    
    idx = 0
    
    def on_key(event):
        nonlocal idx
        if event.key == 'right':
            idx = (idx + 1) % len(indices)
            plt.close()
            fig = visualize_image_pair(indices[idx], save_annotated=save_annotated)
            plt.suptitle(f'Image {indices[idx]+1}/{len(data)}: {data[indices[idx]]["thermal_image"]}', fontsize=14)
            plt.gcf().canvas.mpl_connect('key_press_event', on_key)
            plt.show()
        elif event.key == 'left':
            idx = (idx - 1) % len(indices)
            plt.close()
            fig = visualize_image_pair(indices[idx], save_annotated=save_annotated)
            plt.suptitle(f'Image {indices[idx]+1}/{len(data)}: {data[indices[idx]]["thermal_image"]}', fontsize=14)
            plt.gcf().canvas.mpl_connect('key_press_event', on_key)
            plt.show()
    
    fig = visualize_image_pair(indices[idx], save_annotated=save_annotated)
    plt.suptitle(f'Image {indices[idx]+1}/{len(data)}: {data[indices[idx]]["thermal_image"]}', fontsize=14)
    plt.gcf().canvas.mpl_connect('key_press_event', on_key)
    plt.show()

# Helper function to parse timestamp from the image filename
def parse_timestamp_from_filename(filename):
    # Extract the timestamp from the filename (e.g., HM20240815060955.jpeg)
    base_name = os.path.basename(filename)
    timestamp_str = base_name[2:16]  # Extract "20240815060955"
    return datetime.datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")


# Function to filter images based on a time frame
def filter_images_by_time(data, start_time, end_time):
    filtered_indices = []
    for idx, entry in enumerate(data):
        try:
            baby_id = int(entry["thermal_image"][:2])
            timestamp = parse_timestamp_from_filename(entry["thermal_image"])
            if (start_time <= timestamp <= end_time) and baby_id == 35:
                filtered_indices.append(idx)
        except Exception as e:
            print(f"Error parsing timestamp for entry {idx}: {e}")
    return filtered_indices

def __main__():
    # Example: Specify the time frame
    start_time_str = input("Enter start time (YYYY-MM-DD HH:MM:SS): ").strip()
    end_time_str = input("Enter end time (YYYY-MM-DD HH:MM:SS): ").strip()
    
    try:
        # Parse the input timestamps
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        print(f"Error: {e}. Please ensure the input matches the format 'YYYY-MM-DD HH:MM:SS'.")
        return
    
    # Example: choose whether to save annotated images
    save_ans = input("Save annotated images? (y/n): ").strip().lower()
    save_annotated = (save_ans == 'y')

    # Filter images based on the time frame
    filtered_indices = filter_images_by_time(data, start_time, end_time)
    
    # Browse the filtered images
    browse_images(data, filtered_indices, save_annotated=save_annotated)

# Call the main function to start the visualization
if __name__ == "__main__":
    __main__()

#2024-11-28 05:30:00
#2024-11-28 06:30:00

#2024-09-24 00:00:00
#2024-09-25 00:00:00

#2024-11-26 17:00:00
#2024-11-26 19:00:00

#2024-09-14 09:10:00
#2024-09-14 09:30:00





