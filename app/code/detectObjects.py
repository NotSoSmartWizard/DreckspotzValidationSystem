import logging
import os


# Logger for clearduplicates
current_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(current_dir, "..", "logs")
os.makedirs(logs_dir, exist_ok=True)

detectObjects_logger = logging.getLogger("detectObjects")
detectObjects_log_path = os.path.join(logs_dir, "detectObjectsLog.log")
detectObjects_handler = logging.FileHandler(detectObjects_log_path, mode='w')
detectObjects_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
detectObjects_logger.setLevel(logging.DEBUG)
detectObjects_logger.addHandler(detectObjects_handler)

import glob
import csv
from ultralytics import RTDETR
from waste_mapping import waste_mapping, category_mapping
import pandas as pd

def load_model(rtdetr_path='rtdtrwithaug1106.pt'):
    try:
        return RTDETR(rtdetr_path)
    except Exception as e:
        detectObjects_logger.error(f"Failed to load models: {e}")
        raise


def detect(model, file_path, class_names):
    if not os.path.exists(file_path):
        detectObjects_logger.error(f"File not found: {file_path}")
        return []

    try:
        results = model(file_path)
        detections = [
            {
                'class': class_names[box.cls.item()],
                'confidence': box.conf.item(),
                'bbox': [int(coord) for coord in box.xyxy[0].tolist()]
            }
            for result in results if hasattr(result, 'boxes') and result.boxes is not None
            for box in result.boxes
        ]
        return detections
    except Exception as e:
        detectObjects_logger.error(f"Error processing image {file_path}: {e}")
        return []


def detect_images_in_directory(model, directory_path, class_names, max_images=None, update_progress=None):
    image_files = sorted(glob.glob(os.path.join(directory_path, '*.jpg')))
    total_images = min(len(image_files), max_images) if max_images is not None else len(image_files)
    processed_images = 0
    detectObjects_logger.info(f"Processing up to {max_images if max_images is not None else 'all'} images in {directory_path}")

    all_detections = {}
    for img in image_files[:max_images] if max_images is not None else image_files:
        detections = detect(model, img, class_names)
        all_detections[os.path.basename(img)] = detections
        processed_images += 1
        if update_progress:
            update_progress(processed_images, total_images)

    return all_detections


class_aliases = {
    'plastic_cap': ['big_plastic_cap', 'plastic_cap'],
    'big_plastic_cap': ['big_plastic_cap', 'plastic_cap'],
    'tin_can': ['soda_can', 'tin_can'],
    'soda_can': ['soda_can', 'tin_can'],
    'plastic_cutlery': ['plastic_cutlery', 'plastic_cup'],
    'plastic_cup': ['plastic_cutlery', 'plastic_cup']
    # Add more aliases here
}


def verify_detections(detections, class_name, class_to_category_map):
    correct_labeling = 0
    correct_category = 0
    total_images = len(detections)

    for image_name, detections_list in detections.items():
        correct_labeling_found = False
        correct_category_found = False
        for detection in detections_list:
            detected_class = detection['class']
            detected_category = class_to_category_map.get(detected_class, None)
            actual_class = class_name
            actual_category = class_to_category_map.get(actual_class, None)

            if not correct_labeling_found and detected_class in class_aliases.get(actual_class, [actual_class]):
                correct_labeling += 1
                correct_labeling_found = True

            if not correct_category_found and detected_category == actual_category:
                correct_category += 1
                correct_category_found = True

    return {
        'correct_labeling': correct_labeling,
        'correct_category': correct_category,
        'total_images': total_images
    }


def write_results_to_csv(detections, class_name_of_interest, csv_file_path='detection_results.csv'):
    verified_results = verify_detections(detections, class_name_of_interest, category_mapping)
    total_images = verified_results['total_images']
    correct_labels_count = verified_results['correct_labeling']
    correct_categories_count = verified_results['correct_category']
    label_verify_percentage = (correct_labels_count / total_images) * 100 if total_images > 0 else 0
    category_verify_percentage = (correct_categories_count / total_images) * 100 if total_images > 0 else 0

    try:
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Image Name', 'Class Name', 'Correct Label', 'Detected Classes and Confidences',
                             'Label Verify Percentage', 'Category Verify Percentage'])

            for image_name, result in detections.items():
                detected_info = [f"{d['class']} with confidence {d['confidence']:.2f}" for d in result]
                correct_labeling = any(
                    d['class'] in class_aliases.get(class_name_of_interest, [class_name_of_interest]) for d in result)
                correct_category = all(
                    category_mapping.get(d['class'], None) == category_mapping.get(class_name_of_interest, None) for d
                    in result)
                writer.writerow([image_name, class_name_of_interest, correct_labeling, '; '.join(detected_info),
                                 f"{label_verify_percentage:.2f}%", f"{category_verify_percentage:.2f}%"])
        return label_verify_percentage, category_verify_percentage
    except Exception as e:
        detectObjects_logger.error(f"Failed to write results to CSV for class {class_name_of_interest}: {e}")
        return 0, 0


def process_all_directories(base_directory, model, class_names, output_base_directory, max_images_per_directory=None,
                            update_progress=None):
    output_directory_csv = os.path.join(output_base_directory, 'csv')
    output_directory_progress = os.path.join(output_base_directory, 'progress')
    os.makedirs(output_directory_csv, exist_ok=True)
    os.makedirs(output_directory_progress, exist_ok=True)

    progress_file_path = os.path.join(output_directory_progress, 'progress.txt')
    processed_dirs = set()

    if os.path.exists(progress_file_path):
        with open(progress_file_path, 'r') as file:
            processed_dirs.update(file.read().splitlines())

    class_verification_summary = {}
    total_dirs = sum(len(dirs) for _, dirs, _ in os.walk(base_directory))
    total_images = sum(min(len(glob.glob(os.path.join(root, dir_name, '*.jpg'))),
                           max_images_per_directory) if max_images_per_directory is not None else len(
        glob.glob(os.path.join(root, dir_name, '*.jpg')))
                       for root, dirs, _ in os.walk(base_directory) for dir_name in dirs)
    processed_images = 0

    for root, dirs, _ in os.walk(base_directory):
        for dir_name in dirs:
            directory_path = os.path.join(root, dir_name)

            if directory_path in processed_dirs:
                continue

            if dir_name in waste_mapping:
                class_names_of_interest = waste_mapping[dir_name]
                if not isinstance(class_names_of_interest, list):
                    class_names_of_interest = [class_names_of_interest]  # Ensure it's a list
                for class_name_of_interest in class_names_of_interest:
                    detections = detect_images_in_directory(model, directory_path, class_names,
                                                            max_images_per_directory,
                                                            update_progress=lambda current, total: update_progress(
                                                                processed_images + current, total_images))
                    csv_file_path = os.path.join(output_directory_csv,
                                                 f'{dir_name}_{class_name_of_interest}_results.csv')
                    verify_percentages = write_results_to_csv(detections, class_name_of_interest, csv_file_path)
                    class_verification_summary.setdefault(class_name_of_interest, []).append(verify_percentages)

            processed_images += min(len(glob.glob(os.path.join(root, dir_name, '*.jpg'))),
                                    max_images_per_directory) if max_images_per_directory is not None else len(
                glob.glob(os.path.join(root, dir_name, '*.jpg')))
            if update_progress:
                update_progress(processed_images, total_images)

            with open(progress_file_path, 'a') as file:
                file.write(directory_path + '\n')
                processed_dirs.add(directory_path)
    return class_verification_summary


def process_file(file_path):
    # Load the CSV file
    df = pd.read_csv(file_path)

    # Clean and preprocess the dataframe
    df['Label Verify Percentage'] = df['Label Verify Percentage'].str.replace('%', '').astype(float)
    df['Category Verify Percentage'] = df['Category Verify Percentage'].str.replace('%', '').astype(float)

    # Calculate the summary
    summary = {
        'File Name': os.path.basename(file_path).replace('_results.csv', ''),
        'Class Name': df['Class Name'].mode()[0],  # Most frequent class name
        'Average Label Verify Percentage': df['Label Verify Percentage'].mean(),
        'Average Category Verify Percentage': df['Category Verify Percentage'].mean(),
        'Number of Entries': len(df)
    }

    return summary


def process_directory(directory_path):
    summaries = []
    for filename in os.listdir(directory_path):
        if filename.endswith('_results.csv'):
            file_path = os.path.join(directory_path, filename)
            summary = process_file(file_path)
            summaries.append(summary)

    summary_df = pd.DataFrame(summaries)
    return summary_df
