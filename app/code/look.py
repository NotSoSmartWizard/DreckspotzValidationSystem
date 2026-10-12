import os
import pandas as pd

DATA_DIR = r"C:\studium\bsc_thesis\finaldreckspotzvalidierungssystem-main\app\data\removed_duplicates_export_20220101-20240115"

RESULTS_DIR = r"C:\studium\bsc_thesis\finaldreckspotzvalidierungssystem-main\app\output\removed_duplicates_export_20220101-20240115_1000\csv"

MAX_IMAGES = 1000

total_images = 0
total_with_detection = 0
total_without_detection = 0

for folder_name in os.listdir(DATA_DIR):
    folder_path = os.path.join(DATA_DIR, folder_name)

    if not os.path.isdir(folder_path):
        continue

    # Match your evaluation: sorted and limited to first 1000 images
    image_files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith(".jpg")
    ])[:MAX_IMAGES]

    image_files = set(image_files)

    matching_csvs = [
        f for f in os.listdir(RESULTS_DIR)
        if f.startswith(folder_name + "_")
        and f.endswith("_results.csv")
    ]

    detected_images = set()

    for csv_name in matching_csvs:
        csv_path = os.path.join(RESULTS_DIR, csv_name)
        df = pd.read_csv(csv_path)

        if "Image Name" in df.columns:
            detected_images.update(
                df["Image Name"].dropna().astype(str)
            )

    empty_images = image_files - detected_images

    n_all = len(image_files)
    n_detected = len(image_files & detected_images)
    n_empty = len(empty_images)

    total_images += n_all
    total_with_detection += n_detected
    total_without_detection += n_empty

    print(
        f"{folder_name}: "
        f"evaluated={n_all}, "
        f"with detection={n_detected}, "
        f"no detection={n_empty}"
    )

print("\nTOTAL")
print(f"All evaluated images: {total_images}")
print(f"Images with detection: {total_with_detection}")
print(f"Images with no detection: {total_without_detection}")

if total_images > 0:
    print(
        f"No-detection rate: "
        f"{100 * total_without_detection / total_images:.2f}%"
    )