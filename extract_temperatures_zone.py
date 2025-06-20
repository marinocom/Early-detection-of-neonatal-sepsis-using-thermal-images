import json
import numpy as np
import cv2 as cv

SIDE=1

def create_lut(T_local_min, T_local_max):
    num_pixels = 256
    temperatures = np.linspace(T_local_min, T_local_max, num_pixels)
    return temperatures

def coordinates2temperature(x, y, lut, gray_img):
    """
    Functions to pass from coordinates to temperature you have to pass the lut already created

    """
    gray_img = np.array(gray_img, dtype=np.uint8)
    x_shape, y_shape=gray_img.shape

    x_start = max(y - SIDE, 0)
    x_end = min(y + SIDE + 1, x_shape)
    y_start = max(x - SIDE, 0)
    y_end = min(x + SIDE + 1, y_shape)
    
    region = []
    for i in range(x_start, x_end):
        for j in range(y_start, y_end):
            region.append(gray_img[i, j])

    temperatures = [lut[val] for val in region]

    return max(temperatures)


with open ("min_max_dict.json", "r") as file:
    minmax = json.load(file)

print("min max dict opened\n")

with open ("annotations/time_series_48.json", "r") as file:
    annotations = json.load(file)

print("Annotations file opened\n")

global_max = max([x[1] for x in minmax.values()])
global_min = min([x[0] for x in minmax.values()])

lut = create_lut(global_min,global_max)

print("LUT created\n")

for image in annotations:
    path_image = image['thermal_image']
    for point in image['anotaciones']:
        x, y = point['x'] , point ['y']
        if x:
            try:
                gray_scale_img_path = ("\\data\\uabcvmsc\\cvmsct01\\DATASETS\\NewbornDatasetGrayscale\\" + path_image)
                gray_scale_img_path = gray_scale_img_path.replace("\\", "/")
                gray_img = cv.imread(gray_scale_img_path, cv.IMREAD_GRAYSCALE)
                tmp = coordinates2temperature(x, y, lut, gray_img)
                point['temperature'] = tmp
            except Exception as e:
                print("Exception:", e, "Error with path:", path_image, "points", x, y)
                point['temperature'] = None
        else:
            point['temperature'] = None

with open ("annotations/48_annotated.json", "w") as file:
    json.dump(annotations, file, indent=4)

print("Ended\n")
