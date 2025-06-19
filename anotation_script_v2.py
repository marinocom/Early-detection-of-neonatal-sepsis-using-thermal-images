"""
Thermal and RGB image annotation tool for custom baby datasets.

This program provides a graphical interface to annotate keypoints on thermal images, paired with their corresponding RGB images, enabling the creation of balanced datasets by individual ("baby"). It allows you to:
- Select and visualize thermal and associated RGB images.
- Annotate up to 9 anatomical keypoints per thermal image, with support for skipping points.
- Save annotations in a structured JSON file.
- Track processed images and reasons for exclusion in a CSV file.
- Resume annotation sessions using the CSV tracking file that records which images have already been processed
- Copy annotated (or excluded) images to a destination directory, preserving folder structure.
- Balance image selection to ensure equitable distribution among individuals.
- Support manual selection and robust error handling (missing RGB, already processed images, etc).



Instructions for Using the Image Annotation Program

Overview:
This program allows you to annotate keypoints on thermal images of infants, associating them with corresponding RGB images. Annotations are saved in a structured JSON file, and the program helps balance the dataset across different individuals.

How to Use:

1. Launching the Program:

    - Run the script from the terminal:
       python anotation_script_v2.py
    -Required Files and Directories:

    - Annotation File (.json):  
    The JSON file where all keypoint annotations for the images will be saved.

    - Root Directory of Images:  
    The main directory containing the original thermal and RGB images, organized by individual (baby) or other relevant structure.

    - Personalized Dataset Directory:  
    The output directory where annotated (and skipped) images will be copied, preserving the same folder structure as the Root Directory.

    - Tracking File (.csv):  
    A CSV file used to track annotation progress and metadata. Each row should include:
        - Baby ID
        - Original Thermal Image Path
        - New Thermal Image Path (in the personalized dataset directory)
        - Original RGB Image Path
        - New RGB Image Path (in the personalized dataset directory)
        - Annotations File (JSON)
        - Reason (used to indicate why an image was skipped or to confirm it was annotated)

2. Annotating Images:
   - The program displays a thermal image and its associated RGB image so you can decide to annotate it or not.
   - Click on the thermal image to mark up to 9 anatomical keypoints.
   - To skip an image, use the skip option and select a reason.
   - After annotating you can confirm.

3. Saving and Managing Annotations:
   - Annotations are automatically saved in a JSON file.
   - Skipped images and reasons are logged in a CSV file.
   - Annotated and skipped images are copied to the output directory, preserving the folder structure.

4. Balancing the Dataset:
   - The program automatically selects images to ensure a balanced number per individual.

5. Resuming Work:
   - The program tracks processed images. You can stop and restart without losing progress.

Tips:
- Ensure each thermal image has a corresponding RGB image in the correct location.
- Review the output JSON and CSV files to verify your annotations and skipped images.
- If you encounter errors, check the terminal output for troubleshooting information.

Bug:
- If during the annotation you skip using the right click of the mouse but you are outside the image it leads to an error casue you're outside the boundaries. 

"""

import os
import random
import shutil
import csv
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk, ImageOps, ExifTags
from collections import defaultdict
import threading


# Primero añadir esta función para manejar correctamente orientación EXIF
def apply_exif_orientation(image):
    """
    Aplica manualmente la rotación según la orientación EXIF.
    """
    try:
        exif = image._getexif()
        if exif is not None:
            # Encontrar el tag de orientación
            orientation_tag = None
            for tag, tag_value in ExifTags.TAGS.items():
                if tag_value == 'Orientation':
                    orientation_tag = tag
                    break
            
            if orientation_tag is not None and orientation_tag in exif:
                orientation = exif[orientation_tag]
                
                # Aplicar rotación según la orientación EXIF
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
    except Exception as e:
        print(f"Error al procesar orientación EXIF: {e}")
    
    return image

class LoadingDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Cargando...")
        self.geometry("300x100")
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(pady=20)
        self.label = tk.Label(self, text="Procesando imágenes...")
        self.label.pack()
        self.progress.start()
        self.grab_set()

class AnnotationWindow(tk.Toplevel):
    def __init__(self, parent, thermal_path, rgb_path, on_complete):
        super().__init__(parent)
        self.thermal_path = thermal_path
        self.rgb_path = rgb_path
        self.on_complete = on_complete
        self.annotations = []
        self.current_step = 0
        self.guide_sequence = [
            "Zona1", "CodoIzq", "CodoDer", "RodillaIzq", "RodillaDer",
            "ManoIzq", "ManoDer", "PieIzq", "PieDer"
        ]
        self.class_mapping = [
            "Zona1", "Zona2", "Zona2", "Zona2", "Zona2",
            "Zona3", "Zona3", "Zona3", "Zona3"
        ]
        
        # Cargar la imagen y aplicar rotación EXIF manualmente
        self.thermal_img = Image.open(thermal_path)
        self.thermal_img = apply_exif_orientation(self.thermal_img)
        self.original_width, self.original_height = self.thermal_img.size
        
        # Configuración de escala
        self.max_canvas_width = 800
        self.max_canvas_height = 600
        self.setup_scaling()
        
        self.setup_ui()

    def setup_scaling(self):
        # Calcular relación de aspecto preservando dimensiones
        width_ratio = self.max_canvas_width / self.original_width
        height_ratio = self.max_canvas_height / self.original_height
        self.ratio = min(width_ratio, height_ratio)
        
        self.displayed_width = int(self.original_width * self.ratio)
        self.displayed_height = int(self.original_height * self.ratio)
        
        self.scale_x = self.original_width / self.displayed_width
        self.scale_y = self.original_height / self.displayed_height

    def setup_ui(self):
        self.title("Anotación de puntos")
        self.geometry("1000x600")

        self.image_frame = tk.Frame(self)
        self.image_frame.pack(fill=tk.BOTH, expand=True)

        self.thermal_canvas = tk.Canvas(
            self.image_frame, 
            width=self.max_canvas_width, 
            height=self.max_canvas_height
        )
        self.thermal_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Redimensionar manteniendo relación de aspecto
        resized_thermal = self.thermal_img.resize(
            (self.displayed_width, self.displayed_height),
            Image.Resampling.LANCZOS
        )
        self.thermal_photo = ImageTk.PhotoImage(resized_thermal)
        
        # Centrar la imagen en el canvas
        self.thermal_canvas.create_image(
            (self.max_canvas_width - self.displayed_width) // 2,
            (self.max_canvas_height - self.displayed_height) // 2,
            anchor=tk.NW, 
            image=self.thermal_photo
        )
        
        self.thermal_canvas.bind("<Button-1>", self.on_thermal_click)
        self.thermal_canvas.bind("<Button-3>", self.on_thermal_right_click)

        self.rgb_label = tk.Label(self.image_frame)
        self.rgb_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        # Cargar la imagen RGB y aplicar rotación EXIF manualmente
        rgb_img = Image.open(self.rgb_path)
        rgb_img = apply_exif_orientation(rgb_img)
        rgb_img.thumbnail((800, 600), Image.Resampling.LANCZOS)
        self.rgb_photo = ImageTk.PhotoImage(rgb_img)
        self.rgb_label.config(image=self.rgb_photo)
        
        self.guide_label = tk.Label(self, text=f"Anotar: {self.guide_sequence[self.current_step]}")
        self.guide_label.pack(pady=10)
        self.done_button = tk.Button(self, text="Finalizar", command=self.finalize_annotation)
        self.done_button.pack(pady=10)

    def get_click_position(self, event):
        # Ajustar coordenadas considerando la imagen centrada
        img_x = event.x - (self.max_canvas_width - self.displayed_width) // 2
        img_y = event.y - (self.max_canvas_height - self.displayed_height) // 2
        
        if 0 <= img_x <= self.displayed_width and 0 <= img_y <= self.displayed_height:
            return (
                int(img_x * self.scale_x),
                int(img_y * self.scale_y)
            )
        return None

    def on_thermal_click(self, event):
        pos = self.get_click_position(event)
        if not pos:
            return
        
        x, y = pos
        current_class = self.class_mapping[self.current_step]
        self.annotations.append({"x": x, "y": y, "class": current_class})
        
        # Dibujar punto en posición relativa al canvas
        dot_x = event.x
        dot_y = event.y
        self.thermal_canvas.create_oval(dot_x-3, dot_y-3, dot_x+3, dot_y+3, fill='red', outline='white')
        
        self.current_step += 1
        if self.current_step < len(self.guide_sequence):
            self.guide_label.config(text=f"Anotar: {self.guide_sequence[self.current_step]}")
        else:
            self.guide_label.config(text="Todos los puntos anotados. Presione Finalizar.")

    def on_thermal_right_click(self, event):
        current_class = self.class_mapping[self.current_step]
        self.annotations.append({"x": None, "y": None, "class": "no_present"})
        self.current_step += 1
        if self.current_step < len(self.guide_sequence):
            self.guide_label.config(text=f"Anotar: {self.guide_sequence[self.current_step]}")
        else:
            self.guide_label.config(text="Todos los puntos anotados. Presione Finalizar.")

    def finalize_annotation(self):
        if len(self.annotations) != 9:
            messagebox.showwarning("Atención", "Debe anotar o omitir los 9 puntos.")
            return
        self.on_complete(self.thermal_path, self.rgb_path, self.annotations)
        self.destroy()

class BalancedImageAnnotator:
    def __init__(self, root):
        self.root = root
        self.baby_images = defaultdict(list)
        self.remaining_images = defaultdict(list)
        self.selected_counts = defaultdict(int)
        self.processed = set()
        self.tracking_file = ""
        self.annotations_file = ""
        self.source_dir = ""
        self.dest_dir = ""
        self.current_path = ""
        self.loading_dialog = None
        
        self.setup_gui()
        self.ask_directories()

    def setup_gui(self):
        self.root.title("Image Annotator")
        self.root.geometry("1200x600")

        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(pady=20, expand=True, fill=tk.BOTH)

        self.thermal_panel = tk.Label(self.image_frame)
        self.thermal_panel.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.rgb_panel = tk.Label(self.image_frame)
        self.rgb_panel.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        self.btn_annotate = tk.Button(
            control_frame, 
            text="Anotar (A)", 
            command=self.start_annotation,
            state=tk.DISABLED
        )
        self.btn_annotate.pack(side=tk.LEFT, padx=10)

        self.btn_skip = tk.Button(
            control_frame, 
            text="No Anotar (N)", 
            command=self.handle_no_annotation,
            state=tk.DISABLED
        )
        self.btn_skip.pack(side=tk.LEFT, padx=10)

        self.btn_manual = tk.Button(
            control_frame,
            text="Seleccionar Manualmente (M)",
            command=self.manual_select_image,
            state=tk.DISABLED
        )
        self.btn_manual.pack(side=tk.LEFT, padx=10)

        self.stats_label = tk.Label(self.root, text="")
        self.stats_label.pack(side=tk.BOTTOM, pady=5)

        self.root.bind('a', lambda e: self.start_annotation())
        self.root.bind('n', lambda e: self.handle_no_annotation())
        self.root.bind('m', lambda e: self.manual_select_image())

    def get_rgb_path(self, thermal_path):
        base, ext = os.path.splitext(thermal_path)
        
        # Verificar los dos formatos posibles
        vis_path1 = f"{base}_VIS{ext}"
        vis_path2 = f"{base}.VIS{ext}"
        
        # Verificar caso sensible
        if os.path.exists(vis_path1):
            return vis_path1
        if os.path.exists(vis_path2):
            return vis_path2
        
        # Verificar insensible a mayúsculas/minúsculas
        vis_path1_lower = f"{base}_vis{ext}"
        vis_path2_lower = f"{base}.vis{ext}"
        
        if os.path.exists(vis_path1_lower):
            return vis_path1_lower
        if os.path.exists(vis_path2_lower):
            return vis_path2_lower
        
        return None

    def ask_directories(self):
        self.annotations_file = filedialog.asksaveasfilename(
            title="Seleccione/crea el archivo de anotaciones",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        source_dir = filedialog.askdirectory(title="Seleccione el directorio raíz de las imágenes")
        if not source_dir:
            return
            
        dest_dir = filedialog.askdirectory(title="Seleccione el directorio para el Dataset Personalizado")
        if not dest_dir:
            return
            
        self.tracking_file = filedialog.asksaveasfilename(
                title="Seleccione/crea el archivo de tracking",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")]
            )
        
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        
        self.show_loading_dialog()
        threading.Thread(target=self.initialize_system_thread, daemon=True).start()

    def show_loading_dialog(self):
        self.loading_dialog = LoadingDialog(self.root)
        self.root.after(100, self.loading_dialog.lift)
        # Agregar timeout de 60 segundos para evitar carga infinita
        self.root.after(60000*3, self._timeout_loading_dialog)

    def _timeout_loading_dialog(self):
        if hasattr(self, 'loading_dialog') and self.loading_dialog is not None:
            print("Tiempo de carga excedido - cerrando diálogo forzosamente")
            messagebox.showwarning("Advertencia", "El proceso de carga está tomando demasiado tiempo.\nSe continuará con las imágenes disponibles.")
            self._safely_close_loading_dialog()

    def initialize_system_thread(self):
        try:
            print("Iniciando carga de imágenes...")
            self.load_images()
            print("Imágenes cargadas correctamente")
            
            print("Cargando tracking...")
            self.load_tracking()
            print("Tracking cargado correctamente")
            
            print("Cargando anotaciones existentes...")
            self.load_existing_annotations()
            print("Anotaciones existentes cargadas correctamente")
            
            print("Procesando imágenes por bebé...")
            for baby_id in list(self.baby_images.keys()):
                self.baby_images[baby_id] = [p for p in self.baby_images[baby_id] if p not in self.processed]
                self.remaining_images[baby_id] = self.baby_images[baby_id].copy()
            print("Procesamiento completo")
            
            self.root.after(0, self._safely_enable_and_continue)
        except Exception as e:
            print(f"Error durante la inicialización: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            print("Intentando cerrar diálogo de carga...")
            self.root.after(0, self._safely_close_loading_dialog)

    def _safely_close_loading_dialog(self):
        try:
            if hasattr(self, 'loading_dialog') and self.loading_dialog is not None:
                self.loading_dialog.destroy()
                print("Diálogo de carga cerrado correctamente")
        except Exception as e:
            print(f"Error al cerrar diálogo de carga: {str(e)}")
    
    def _safely_enable_and_continue(self):
        try:
            self.enable_buttons()
            self.next_image()
            print("Interfaz inicializada correctamente")
        except Exception as e:
            print(f"Error al habilitar interfaz: {str(e)}")
            messagebox.showerror("Error", f"Error al inicializar interfaz: {str(e)}")

    def load_existing_annotations(self):
        if os.path.exists(self.annotations_file):
            try:
                with open(self.annotations_file, 'r') as f:
                    existing_annotations = json.load(f)
                    for entry in existing_annotations:
                        thermal_path = os.path.join(self.source_dir, entry['thermal_image'])
                        self.processed.add(thermal_path)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

    def enable_buttons(self):
        self.btn_annotate.config(state=tk.NORMAL)
        self.btn_skip.config(state=tk.NORMAL)
        self.btn_manual.config(state=tk.NORMAL)

    def load_images(self):
        image_exts = ('.jpg', '.jpeg', '.png')
        for root, _, files in os.walk(self.source_dir):
            for f in files:
                # Solo procesamos archivos de imagen que no sean VIS
                if f.lower().endswith(image_exts) and not ('_vis' in f.lower() or '.vis' in f.lower()):
                    thermal_path = os.path.join(root, f)
                    
                    # Verificamos que exista una imagen RGB correspondiente
                    rgb_path = self.get_rgb_path(thermal_path)
                    if rgb_path:
                        baby_id = self.get_baby_id(thermal_path)
                        self.baby_images[baby_id].append(thermal_path)

    def load_tracking(self):
        if os.path.exists(self.tracking_file):
            with open(self.tracking_file, 'r', newline='') as f:
                reader = csv.reader(f)
                try:
                    headers = next(reader)
                    for row in reader:
                        baby_id = row[0]
                        thermal_path = row[1]
                        self.processed.add(thermal_path)
                        self.selected_counts[baby_id] += 1
                except StopIteration:
                    pass

    def get_baby_id(self, path):
        relative_path = os.path.relpath(path, self.source_dir)
        return relative_path.split(os.sep)[0]

    def select_next_image(self):
        weights = {}
        total_weight = 0
        for baby_id, images in self.remaining_images.items():
            if images:
                weight = 1 / (self.selected_counts.get(baby_id, 0) + 1)
                weights[baby_id] = weight
                total_weight += weight
        
        if not weights:
            return None
        
        rand = random.uniform(0, total_weight)
        current = 0
        selected_baby = None
        for baby_id, weight in weights.items():
            if current + weight >= rand:
                selected_baby = baby_id
                break
            current += weight
        
        if selected_baby and self.remaining_images[selected_baby]:
            return random.choice(self.remaining_images[selected_baby])
        return None

    def show_image(self, thermal_path):
        try:
            def load_images():
                # Cargar imagen térmica y aplicar rotación EXIF manualmente
                thermal_img = Image.open(thermal_path)
                thermal_img = apply_exif_orientation(thermal_img)
                thermal_img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                thermal_photo = ImageTk.PhotoImage(thermal_img)

                rgb_path = self.get_rgb_path(thermal_path)
                if not rgb_path:
                    raise FileNotFoundError("No se encontró imagen RGB correspondiente")

                # Cargar imagen RGB y aplicar rotación EXIF manualmente
                rgb_img = Image.open(rgb_path)
                rgb_img = apply_exif_orientation(rgb_img)
                rgb_img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                rgb_photo = ImageTk.PhotoImage(rgb_img)

                self.root.after(0, self.update_display, thermal_photo, rgb_photo, thermal_path)

            threading.Thread(target=load_images, daemon=True).start()
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            self.next_image()

    def update_display(self, thermal_photo, rgb_photo, thermal_path):
        self.thermal_panel.config(image=thermal_photo)
        self.thermal_panel.image = thermal_photo
        self.rgb_panel.config(image=rgb_photo)
        self.rgb_panel.image = rgb_photo
        self.current_path = thermal_path
        self.update_stats()

    def update_stats(self):
        total_selected = sum(self.selected_counts.values())
        stats_text = f"Total procesadas: {total_selected} | "
        stats_text += " | ".join(f"Bebé {k}: {v}" for k, v in sorted(self.selected_counts.items()) if v > 0)
        self.stats_label.config(text=stats_text)

    def start_annotation(self):
        thermal_path = self.current_path
        rgb_path = self.get_rgb_path(thermal_path)
        if not rgb_path:
            messagebox.showerror("Error", "Imagen RGB no encontrada")
            return
        AnnotationWindow(self.root, thermal_path, rgb_path, self.on_annotation_complete)

    def on_annotation_complete(self, thermal_path, rgb_path, annotations):
        new_entry = {
            "thermal_image": os.path.relpath(thermal_path, self.source_dir),
            "rgb_image": os.path.relpath(rgb_path, self.source_dir),
            "anotaciones": [{
                "x": ann['x'],
                "y": ann['y'],
                "class": ann['class'] if ann['class'] != 'no_present' else 'no_present'
            } for ann in annotations]
        }

        all_annotations = []
        if os.path.exists(self.annotations_file):
            try:
                with open(self.annotations_file, 'r') as f:
                    all_annotations = json.load(f)
            except json.JSONDecodeError:
                pass
        
        all_annotations.append(new_entry)
        
        with open(self.annotations_file, 'w') as f:
            json.dump(all_annotations, f, indent=4, ensure_ascii=False)

        thermal_dest = os.path.join(self.dest_dir, os.path.relpath(thermal_path, self.source_dir))
        os.makedirs(os.path.dirname(thermal_dest), exist_ok=True)
        shutil.copy2(thermal_path, thermal_dest)

        rgb_dest = os.path.join(self.dest_dir, os.path.relpath(rgb_path, self.source_dir))
        os.makedirs(os.path.dirname(rgb_dest), exist_ok=True)
        shutil.copy2(rgb_path, rgb_dest)

        baby_id = self.get_baby_id(thermal_path)
        with open(self.tracking_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if os.stat(self.tracking_file).st_size == 0:
                writer.writerow(["Baby ID", "Original Thermal Path", "New Thermal Path", 
                               "Original RGB Path", "New RGB Path", "Annotations File", "Reason"])
            writer.writerow([baby_id, thermal_path, thermal_dest, 
                           rgb_path, rgb_dest, self.annotations_file, ""])

        self.selected_counts[baby_id] += 1
        self.processed.add(thermal_path)
        self.processed.add(rgb_path)
        if thermal_path in self.remaining_images[baby_id]:
            self.remaining_images[baby_id].remove(thermal_path)

        self.next_image()

    def handle_no_annotation(self):
        reason = simpledialog.askstring("Motivo", "Ingrese el motivo para no anotar:")
        if not reason:
            return

        thermal_path = self.current_path
        rgb_path = self.get_rgb_path(thermal_path)
        if not rgb_path:
            messagebox.showerror("Error", "Imagen RGB no encontrada")
            return

        thermal_relative = os.path.relpath(thermal_path, self.source_dir)
        thermal_dest = os.path.join(self.dest_dir, reason, thermal_relative)
        os.makedirs(os.path.dirname(thermal_dest), exist_ok=True)
        shutil.copy2(thermal_path, thermal_dest)

        rgb_relative = os.path.relpath(rgb_path, self.source_dir)
        rgb_dest = os.path.join(self.dest_dir, reason, rgb_relative)
        os.makedirs(os.path.dirname(rgb_dest), exist_ok=True)
        shutil.copy2(rgb_path, rgb_dest)

        baby_id = self.get_baby_id(thermal_path)
        with open(self.tracking_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if os.stat(self.tracking_file).st_size == 0:
                writer.writerow(["Baby ID", "Original Thermal Path", "New Thermal Path", 
                               "Original RGB Path", "New RGB Path", "Annotations File", "Reason"])
            writer.writerow([baby_id, thermal_path, thermal_dest, 
                           rgb_path, rgb_dest, self.annotations_file, reason])

        self.processed.add(thermal_path)
        self.processed.add(rgb_path)
        if thermal_path in self.remaining_images[baby_id]:
            self.remaining_images[baby_id].remove(thermal_path)
        self.next_image()

    def manual_select_image(self):
        thermal_path = filedialog.askopenfilename(
            title="Seleccionar imagen térmica para anotar",
            initialdir=self.source_dir,
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if not thermal_path:
            return
        
        thermal_path = os.path.normpath(thermal_path)
        
        if not thermal_path.startswith(os.path.abspath(self.source_dir) + os.sep):
            messagebox.showerror("Error", "La imagen debe estar dentro del directorio fuente seleccionado.")
            return
        
        if thermal_path in self.processed:
            messagebox.showinfo("Información", "Esta imagen ya ha sido procesada.")
            return
        
        rgb_path = self.get_rgb_path(thermal_path)
        if not rgb_path:
            messagebox.showerror("Error", "No se encontró la imagen RGB correspondiente.")
            return
        
        self.current_path = thermal_path
        self.show_image(thermal_path)

    def next_image(self):
        self.current_path = self.select_next_image()
        if self.current_path:
            self.show_image(self.current_path)
        else:
            messagebox.showinfo("Fin", "¡Todas las imágenes han sido procesadas!")
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = BalancedImageAnnotator(root)
    root.mainloop()