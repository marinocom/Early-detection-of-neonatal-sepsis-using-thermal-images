import json

with open('annotations/final.json', 'r') as file:
    data = json.load(file)

filtered_data = []

for image in data:
    point=False
    for bodypart in image["anotaciones"]:
        if(bodypart["temperature"] is not None):
            point=True

    if point:
        filtered_data.append(image)

with open ("annotations/final_dataset_annotated_zone_v2.json", "w") as file:
    json.dump(filtered_data, file, indent=4)
