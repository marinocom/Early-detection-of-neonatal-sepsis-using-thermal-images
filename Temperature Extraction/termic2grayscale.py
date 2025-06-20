import json
import numpy as np
import cv2
import os
import easyocr
from scipy.spatial import KDTree

reader=easyocr.Reader(['en'], model_storage_directory="./.EasyOCR/model/", download_enabled=False)

def extract_min_max(img_path,reader):
    """
    Extrae los valores de temperatura mínima y máxima desde una imagen con barra de color.

    Args:
        img_path (str): Ruta de la imagen.
        reader (easyocr.Reader): Lector OCR para extraer los números.

    Returns:
        tuple: (temperatura mínima, temperatura máxima) como float.
    """
    img=cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    array=np.array(img, dtype=np.uint8)

    array_max=array[140: 170, 15:90]
    if array.shape==(480, 640):
        array_min=array[393: 420, 15:90]
        
    elif array.shape==(640, 480):
        array_min=array[460: 485, 15:90]
        
    else:
        print("Hay un intruso en el tamaño de la imagen\n")

    _, max_binary=cv2.threshold(array_max, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    _, min_binary=cv2.threshold(array_min, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    min=reader.readtext(min_binary)[0][1]
    max=reader.readtext(max_binary)[0][1]

    if "," in max:
        max=max.replace(",", "")
    
    if "," in min:
        min=min.replace(",", "") 

    return float(min), float(max)

def create_min_max_dict():
    """
    Crea un diccionario con las rutas de imágenes y sus temperaturas mínimas y máximas.

    Returns:
        dict: Claves son rutas de imagen y valores son listas [min, max].
    """
    dict={}
    babies_folder_path=r"/data/uabcvmsc/shared/newborn"
    for babies in os.listdir(babies_folder_path):
        print(babies, "\n")
        folder_path=os.path.join(babies_folder_path, babies)
        if not os.path.isdir(folder_path):
            continue
        for date in os.listdir(folder_path):
            date_path=os.path.join(folder_path, date)
            for file in os.listdir(date_path):
                img_path=os.path.join(date_path,file)
                if("VIS" not in img_path and ".jpeg" in img_path):
                    try:
                        img_min, img_max=extract_min_max(img_path, reader)

                        if img_min>100:
                            img_min=img_min/10
                        
                        if img_max>100:
                            img_max=img_max/10
                        
                        if 10<img_min<40 and  30<img_max<50:
                            dict[img_path]=[img_min, img_max]
                    except:
                        print("\nError with image: ", img_path)
    return dict

def create_lut(gradient_column, T_local_min, T_local_max):
    """
    Crea una tabla de búsqueda (Lookup Table, LUT) que asocia colores con temperaturas.

    Args:
        gradient_column (numpy.ndarray): Columna de la barra de gradiente (H,1,3).
        T_local_min (float): Temperatura mínima de la imagen.
        T_local_max (float): Temperatura máxima de la imagen.

    Returns:
        dict: Diccionario que asocia colores RGB (tupla) con temperaturas (float).
    """
    num_pixels = gradient_column.shape[0]
    temperatures = np.linspace(T_local_min, T_local_max, num_pixels)
    temperatures = temperatures[::-1]
    
    return {tuple(gradient_column[i, 0, :]): temperatures[i] for i in range(num_pixels)}

def normalize_to_global(temp_image, T_global_min, T_global_max):
    """
    Normaliza una imagen de temperaturas a una escala de grises global.

    Args:
        temp_image (numpy.ndarray): Imagen con valores de temperatura.
        T_global_min (float): Temperatura mínima global.
        T_global_max (float): Temperatura máxima global.

    Returns:
        numpy.ndarray: Imagen en escala de grises (uint8).
    """
    grayscale = ((temp_image - T_global_min) / (T_global_max - T_global_min) * 255).clip(0, 255).astype(np.uint8)
    return grayscale

def aplicar_lut(imagen_rgb, lut):
    """
    Convierte una imagen RGB a temperaturas usando una Lookup Table (LUT).
    
    Args:
        imagen_rgb (numpy.ndarray): Imagen en formato RGB (shape: HxWx3).
        lut (dict): Diccionario que mapea colores (tuplas RGB) a temperaturas.
    
    Returns:
        numpy.ndarray: Matriz de temperaturas (shape: HxW).
    """
    colors_lut = np.array(list(lut.keys()))
    temps_lut = np.array(list(lut.values()))
    
    kdtree = KDTree(colors_lut)
    
    h, w = imagen_rgb.shape[:2]
    pixels = imagen_rgb.reshape(-1, 3)
    
    _, indices = kdtree.query(pixels)
    
    temp_image = temps_lut[indices].reshape(h, w)
    
    return temp_image

def termic2grayscale(dict, global_min, global_max):
    """
    Convierte imágenes térmicas RGB a imágenes en escala de grises,
    normalizadas a un rango global.

    Args:
        dict (dict): Diccionario con rutas de imagen y sus [min, max] de temperatura.
        global_min (float): Temperatura mínima global.
        global_max (float): Temperatura máxima global.

    Returns:
        None. Las imágenes normalizadas se guardan en disco.
    """
    for img_path in dict.keys():
        img=cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)
        if(img.shape==(480, 640)):
            gradient_bar=img[182:446, 15:26, :]
        else:
            gradient_bar=img[182:382, 10:26, :]
        
        gradient_column=gradient_bar[:,5,:].reshape(-1, 1, 3)

        lut_img=create_lut(gradient_column, dict[img_path][0], dict[img_path][1])

        temp_img=aplicar_lut(img, lut_img)
        
        grayscale_img=normalize_to_global(temp_img, T_global_min=global_min, T_global_max=global_max)

        relative_path = os.path.relpath(img_path, start="/data/uabcvmsc/shared/newborn")

        output_path = os.path.join("NewbornDatasetGrayscale", relative_path)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        cv2.imwrite(output_path, grayscale_img)

if os.path.exists("min_max_dict.json"):
    with open("min_max_dict.json", "r", encoding="utf-8") as file:
        min_max_dict=json.load(file)
    print("Min Max Dict already existed.")
else:
    print("Creating Min Max Dict")
    min_max_dict=create_min_max_dict()
    with open("min_max_dict.json", "w", encoding="utf-8") as file:
        json.dump(min_max_dict, file)

print("Starting the conversion \n")

termic2grayscale(min_max_dict, min([x[0] for x in min_max_dict.values()]), max([x[1] for x in min_max_dict.values()]))
