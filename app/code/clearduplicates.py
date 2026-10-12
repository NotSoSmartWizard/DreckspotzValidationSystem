import logging
import os

# Logger for clearduplicates
current_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(current_dir, "..", "logs")
os.makedirs(logs_dir, exist_ok=True)

clearduplicates_logger = logging.getLogger("clearduplicates")
clearduplicates_log_path = os.path.join(logs_dir, "clearduplicatesLog.log")
clearduplicates_handler = logging.FileHandler(clearduplicates_log_path, mode='w')
clearduplicates_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
clearduplicates_logger.setLevel(logging.DEBUG)
clearduplicates_logger.addHandler(clearduplicates_handler)


import pandas as pd
from geopy.distance import geodesic
from datetime import timedelta

def parse_date(date_str):
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M"]
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt, dayfirst=("." in fmt))
        except ValueError:
            continue
    # If none of the formats match, coerce to NaT
    return pd.to_datetime(date_str, errors='coerce')

def remove_duplicates(df, output_path, duration_minutes=10, radius_meters=1, update_progress=lambda x, y: None):
    if 'SPOTTED_AT' not in df.columns or df['SPOTTED_AT'].isna().all():
        clearduplicates_logger.error("'SPOTTED_AT' column is missing or entirely invalid.")
        return

    try:
        df['SPOTTED_AT'] = df['SPOTTED_AT'].apply(parse_date)
    except Exception as e:
        clearduplicates_logger.error(f"Error converting 'SPOTTED_AT' to datetime: {e}")
        return

    # Ensure LATITUDE and LONGITUDE are numeric
    df['LATITUDE'] = pd.to_numeric(df['LATITUDE'], errors='coerce')
    df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')

    # Filter out invalid coordinates
    invalid_coords = len(df) - len(df[(df['LATITUDE'].between(-90, 90)) & (df['LONGITUDE'].between(-180, 180))])
    clearduplicates_logger.info(f"Filtered out {invalid_coords} rows due to invalid coordinates.")
    df = df[(df['LATITUDE'].between(-90, 90)) & (df['LONGITUDE'].between(-180, 180))].copy()
    df = df[df['SPOTTED_AT'].notna()]  # Drop rows with invalid dates
    initial_count = len(df)

    clearduplicates_logger.info(f"Initial record count: {initial_count}")

    # Grouping data
    grouped = df.groupby(['LITTER_CATEGORY_PRESELECT', 'LITTER_CATEGORY'])
    clearduplicates_logger.info(f"Total groups created: {len(grouped)}")

    to_drop = set()
    total_groups = len(grouped)
    processed_groups = 0

    for name, group in grouped:
        sorted_group = group.sort_values('SPOTTED_AT')
        times = sorted_group['SPOTTED_AT'].values

        for i in range(len(sorted_group)):
            if sorted_group.index[i] in to_drop:
                continue
            for j in range(i + 1, len(sorted_group)):
                if sorted_group.index[j] in to_drop:
                    continue
                time_diff = abs(pd.to_datetime(times[j]) - pd.to_datetime(times[i]))
                if time_diff > timedelta(minutes=duration_minutes):
                    break  # No need to compare further
                if is_within_radius(sorted_group.iloc[i]['LATITUDE'], sorted_group.iloc[i]['LONGITUDE'],
                                    sorted_group.iloc[j]['LATITUDE'], sorted_group.iloc[j]['LONGITUDE'],
                                    radius=radius_meters):
                    to_drop.add(sorted_group.index[j])
                    clearduplicates_logger.info(
                        f"Duplicate found and removed: {sorted_group.iloc[j].name} (URL: {sorted_group.iloc[j]['IMAGE']}) due to proximity with {sorted_group.iloc[i].name} (URL: {sorted_group.iloc[i]['IMAGE']}). Details: Time={sorted_group.iloc[i]['SPOTTED_AT']}, Category={sorted_group.iloc[i]['LITTER_CATEGORY']}")

        processed_groups += 1
        if processed_groups % 10 == 0:  # Update progress every 10 groups
            update_progress(processed_groups, total_groups)

    update_progress(total_groups, total_groups)  # Ensure progress is 100% at the end

    try:
        if not output_path:
            clearduplicates_logger.error("Output path is not specified.")
            return
        if os.path.dirname(output_path):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_clean = df.drop(to_drop)
        df_clean.to_csv(output_path, index=False)
    except Exception as e:
        clearduplicates_logger.error(f"Error saving cleaned data to {output_path}: {e}")
        return

    duplicates_removed = len(to_drop)
    clearduplicates_logger.info(f"Total records processed: {initial_count}")
    clearduplicates_logger.info(f"Total duplicates removed: {duplicates_removed}")
    clearduplicates_logger.info(f"Cleaned data saved to {output_path}")

def is_within_radius(lat1, lon1, lat2, lon2, radius=1):
    try:
        distance = geodesic((lat1, lon1), (lat2, lon2)).meters
        clearduplicates_logger.debug(f"Distance between ({lat1}, {lon1}) and ({lat2}, {lon2}): {distance} meters")
        return distance <= radius
    except ValueError as e:
        clearduplicates_logger.warning(f"Invalid coordinates skipped: ({lat1}, {lon1}), ({lat2}, {lon2})")
        return False

if __name__ == "__main__":
    input_path = "../testdata/export_20220101-20240115.csv"
    if not os.path.exists(input_path):
        clearduplicates_logger.error(f"The file {input_path} does not exist.")
        exit(1)

    output_path = "testdata/cleaned_data.csv"

    # Adjustable parameters for time duration and radius
    duration_minutes = 10
    radius_meters = 5

    try:
        df = pd.read_csv(input_path, low_memory=False)
        remove_duplicates(df, output_path, duration_minutes=duration_minutes, radius_meters=radius_meters)
    except Exception as e:
        clearduplicates_logger.error(f"Error reading input file {input_path}: {e}")
