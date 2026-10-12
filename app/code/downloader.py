import logging
import os

# Logger for downloader

current_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(current_dir, "..", "logs")
os.makedirs(logs_dir, exist_ok=True)

downloader_logger = logging.getLogger("downloader")
downloader_log_path = os.path.join(logs_dir, "downloaderLog.log")
downloader_handler = logging.FileHandler(downloader_log_path, mode='w')
downloader_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
downloader_logger.setLevel(logging.DEBUG)
downloader_logger.addHandler(downloader_handler)

import os
import pandas as pd
import re
import threading
import concurrent.futures
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io import StringIO

def handle_csv_file(file_path):
    encodings = ['utf-8', 'latin1', 'iso-8859-1']
    delimiters = [',', ';']

    for encoding in encodings:
        for delimiter in delimiters:
            try:
                if not os.path.isfile(file_path):
                    raise FileNotFoundError(f"No such file or directory: '{file_path}'")

                with open(file_path, 'rb') as file:
                    byte_content = file.read()

                content = byte_content.decode(encoding, errors='replace')

                data = pd.read_csv(StringIO(content), delimiter=delimiter, on_bad_lines='skip', low_memory=False)

                downloader_logger.info(f"CSV loaded successfully with {encoding} encoding and '{delimiter}' delimiter.")

                print(f"DataFrame columns with {encoding} encoding and '{delimiter}' delimiter:")
                print(data.columns)

                if len(data.columns) == 1 and delimiter == ',':
                    downloader_logger.warning(f"Failed to parse with {delimiter} delimiter, retrying with next delimiter")
                    continue

                if len(data.columns) == 1:
                    downloader_logger.warning(f"Parsing failed with encoding {encoding} and delimiter {delimiter}")
                    continue

                date_columns = ['CREATED_AT', 'MODIFIED_AT', 'SPOTTED_AT']
                for column in date_columns:
                    if column in data.columns:
                        data[column] = pd.to_datetime(data[column], errors='coerce', dayfirst=True)

                return data
            except FileNotFoundError as e:
                downloader_logger.error(e)
                return None
            except UnicodeDecodeError as e:
                downloader_logger.error(f"Decoding failed for encoding {encoding}: {e}")
            except pd.errors.ParserError as e:
                downloader_logger.error(f"Parsing failed for delimiter '{delimiter}': {e}")
            except Exception as e:
                downloader_logger.error(f"Failed to load CSV with {encoding} encoding and '{delimiter}' delimiter: {e}")

    downloader_logger.error("Failed to load CSV with all attempted encodings and delimiters.")
    return None


def clean_folder_name(name):
    return re.sub(r'[<>:"/\|?*]', '', name)


def download_data(data, app, csv_file_name, update_progress):
    csv_base_name = os.path.splitext(os.path.basename(csv_file_name))[0]  # Extracts file name without extension
    base_dir = os.path.join(current_dir,"..", "data", csv_base_name)  # Uses CSV file name for the folder
    images_data = list(prepare_download(data, base_dir))
    total_images = len(images_data)
    downloaded_files = []
    skipped_files = []
    download_count = 0
    skip_count = 0
    lock = threading.Lock()

    dataset_name = f"{csv_base_name} dataset"  # Dynamic dataset name for display

    print(f"Starting download of {total_images} images from {dataset_name}...")


    def download_and_track(img_data):
        nonlocal download_count, skip_count
        image_url, folder_path = img_data
        file_name = os.path.basename(urlparse(image_url).path)
        file_path = os.path.join(folder_path, file_name)

        if os.path.exists(file_path):
            with lock:
                skipped_files.append(file_name)
                skip_count += 1
                if (download_count + skip_count) % 10 == 0:
                    update_progress(download_count + skip_count, total_images)
            return file_name

        result = download_image(img_data)
        if result:
            with lock:
                downloaded_files.append(result)
                download_count += 1
                if (download_count + skip_count) % 10 == 0:
                    update_progress(download_count + skip_count, total_images)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(download_and_track, images_data)

    update_progress(total_images, total_images)
    if len(downloaded_files) + len(skipped_files) == total_images:
        downloader_logger.info(f"All images from {dataset_name} processed successfully.")
    else:
        missing_count = total_images - (len(downloaded_files) + len(skipped_files))
        downloader_logger.warning(f"Some images from {dataset_name} failed to download: {missing_count} failures.")


def prepare_download(data, base_dir):
    for index, row in data.iterrows():
        image_url = row['IMAGE']
        if pd.notna(image_url):
            litter_category_preselect = row['LITTER_CATEGORY_PRESELECT']
            litter_category = row['LITTER_CATEGORY']

            if pd.isna(litter_category_preselect) or (isinstance(litter_category, str) and litter_category.lower() == 'other') or pd.isna(litter_category):
                continue

            category = clean_folder_name(f"{litter_category_preselect}_{litter_category}")
            category_dir = os.path.join(base_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            yield (image_url, category_dir)



def download_image(image_data):
    image_url, folder_path = image_data
    if not image_url.lower().startswith(('http://', 'https://')):
        downloader_logger.error(f"Invalid URL: {image_url}")
        return None

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    file_name = os.path.basename(urlparse(image_url).path)
    file_path = os.path.join(folder_path, file_name)

    if os.path.exists(file_path):
        return file_name

    try:
        response = session.get(image_url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            downloader_logger.info(f"Downloaded {file_name}")
            return file_name
        else:
            downloader_logger.error(f"Failed to download {image_url}. Status code: {response.status_code}")
    except requests.exceptions.Timeout:
        downloader_logger.error(f"Timeout occurred while downloading {image_url}")
    except requests.exceptions.RequestException as e:
        downloader_logger.error(f"Error downloading {image_url}: {e}")

    return None

