# DreckspotzValidationSystem

A Python-based graphical user interface for downloading, processing, and validating litter data from the Dreckspotz app using the RT-DETR object detection algorithm.

## Description

The DreckspotzValidationSystem is designed to analyze and validate user-submitted litter classifications from the Dreckspotz app.

The application provides the following functionality:

- **CSV Import:** Load a dataset containing litter classifications, image URLs, timestamps, and geographic coordinates.
- **Duplicate Removal (optional):** Identify and remove potentially duplicate entries based on location, time, and litter category.
- **Image Download:** Download images referenced in the CSV file and organize them into folders based on their assigned litter categories.
- **Object Detection:** Analyze the downloaded images using a trained RT-DETR model.
- **Classification Validation:** Compare detected objects with the original user-assigned labels and their corresponding higher-level waste categories.
- **Results Export:** Generate CSV files containing the validation results and summary statistics.

## Installation

### Prerequisites

- Python 3
- pip (Python package manager)

### Setup

1. Clone this repository:

   ```bash
   git clone <repository-url>
   ```

2. Navigate to the repository directory:

   ```bash
   cd DreckspotzValidationSystem
   ```

3. Install the required Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Dataset Requirements

**The original Dreckspotz dataset is private and is not included in this repository.** No sample or test dataset containing real user submissions is provided.

To use the application, you must supply your own CSV file with the required columns and valid image URLs.

### Required CSV Columns

The following columns must be present with exactly these names:

| Column | Description |
|---|---|
| `LATITUDE` | Latitude of the reported litter location |
| `LONGITUDE` | Longitude of the reported litter location |
| `SPOTTED_AT` | Date and time when the litter was spotted |
| `LITTER_CATEGORY_PRESELECT` | Higher-level litter category |
| `LITTER_CATEGORY` | Specific litter classification |
| `IMAGE` | URL pointing to the corresponding litter image |

### CSV Format

The CSV file must contain a header row with the required column names.

Both comma-separated (`,`) and semicolon-separated (`;`) CSV files are supported.

The data must meet the following requirements:

- **Coordinates:** `LATITUDE` and `LONGITUDE` must contain valid geographic coordinates. Latitude must be between -90 and 90, and longitude between -180 and 180.
- **Timestamps:** `SPOTTED_AT` must contain a valid date and time. Supported formats include `YYYY-MM-DD HH:MM:SS`, `YYYY-MM-DD HH:MM`, and `DD.MM.YYYY HH:MM`.
- **Categories:** `LITTER_CATEGORY_PRESELECT` and `LITTER_CATEGORY` must contain category names compatible with the mappings defined in `waste_mapping.py`.
- **Images:** `IMAGE` must contain a valid, accessible HTTP or HTTPS URL pointing to an image. The object detection process analyzes downloaded `.jpg` files.

Additional columns may be included and do not need to be removed.

For reference, an input CSV can use the following header:

```csv
LATITUDE;LONGITUDE;SPOTTED_AT;LITTER_CATEGORY_PRESELECT;LITTER_CATEGORY;IMAGE
```

This example only describes the required structure. It does not contain any real or synthetic dataset entries.

## Usage

### 1. Start the Application

Navigate to the `app/code` directory:

```bash
cd app/code
```

Start the application on Linux:

```bash
python3 main.py
```

Or on Windows:

```bash
python main.py
```

The graphical user interface will open.

### 2. Import a CSV File

Click **Insert CSV Data** and select your CSV file.

Ensure that the file contains the required columns described in the Dataset Requirements section.

### 3. Remove Duplicates (Optional)

Click **Clear Duplicates** to identify and remove potentially duplicate entries before downloading images.

Two entries are considered potential duplicates when:

- They belong to the same litter category and subcategory.
- Their geographic coordinates are within a radius of 10 meters.
- Their timestamps are within 30 minutes of each other.

When duplicates are detected, only one entry is retained.

The cleaned dataset is saved as a separate CSV file with the prefix `removed_duplicates_`.

**Note:** Duplicate removal is optional. Because entries can be incorrectly identified as duplicates, this step may remove valid submissions. Entries with invalid coordinates or timestamps are also excluded during this process.

You can skip this step and proceed directly to downloading the images.

### 4. Download Images

Click **Download Data** to download the images referenced in the CSV file.

The application automatically organizes the downloaded images into folders based on their original litter classifications.

Files are stored in:

```text
app/data/<dataset_name>/
```

Each category is stored in a separate subdirectory.

Entries with missing categories or categories excluded by the download logic are skipped. Images must be accessible through their supplied URLs.

### 5. Run Object Detection

After downloading the images, click **Detect Data**.

You can specify the maximum number of images to analyze per category or select **MAX** to analyze all available images.

The application uses a trained RT-DETR model to detect objects in the downloaded images.

For each category, the detected objects are compared against:

- **Specific litter classification:** Whether an expected object class is detected in the image.
- **Higher-level waste category:** Whether the detected object belongs to the expected broader waste category.

The mappings between the original litter classifications and the model classes are defined in `waste_mapping.py`.

### 6. View Results

After processing, the application generates CSV files containing the validation results.

Results are saved in:

```text
app/output/<dataset_name>_<image_limit>/
```

The output includes:

- `csv/` — Individual CSV files containing detected object classes, confidence scores, and validation results.
- `summary_results.csv` — A summary of the validation percentages and the number of evaluated images per class.
- `progress/` — Progress information used to track processed directories.

The results can be used to evaluate the consistency between the original user-submitted litter classifications and the predictions made by the RT-DETR model.

## Data Privacy

The Dreckspotz dataset contains user-generated submissions and is not publicly distributed as part of this repository.

For this reason:

- No original Dreckspotz CSV exports are included.
- No user-submitted images or private test datasets are provided.
- Users must provide their own appropriately authorized data to run the application.
- Downloaded data and generated analysis results are stored locally.

The application is intended for research and data validation purposes. Users are responsible for ensuring that they have permission to access and process the datasets and image URLs they provide.

## Notes

- The category mappings in `waste_mapping.py` may need to be adapted when working with datasets that use different category names.
- A matching object detection does not necessarily prove that the original user classification is correct, as multiple objects may appear in one image.


