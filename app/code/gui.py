import logging
import os

# Ensure 'logs' directory exists
current_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(current_dir, "..", "logs")
os.makedirs(logs_dir, exist_ok=True)

# Logger for GUI
gui_logger = logging.getLogger("gui")
gui_log_path = os.path.join(logs_dir, "guiLog.log")
gui_handler = logging.FileHandler(gui_log_path, mode='w')
gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
gui_logger.setLevel(logging.DEBUG)
gui_logger.addHandler(gui_handler)





import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import time
import glob

from downloader import handle_csv_file, download_data
from detectObjects import load_model, process_all_directories, process_directory
from clearduplicates import remove_duplicates



def create_main_frame(app):
    gui_logger.info("Starting the GUI application")
    app.title("Data Verification")
    app.geometry("600x500")
    ctk.set_appearance_mode("dark")

    label = ctk.CTkLabel(app, text="Data Verification", font=("Arial", 16))
    label.pack(pady=20)

    load_button = ctk.CTkButton(app, text="Insert CSV Data", command=lambda: load_csv_event(app))
    load_button.pack(pady=10)

    clear_duplicates = ctk.CTkButton(app, text="Clear Duplicates", command=lambda: clear_duplicates_thread(app),
                                     state='disabled')
    clear_duplicates.pack(pady=10)

    download_button = ctk.CTkButton(app, text="Download Data", state='disabled',
                                    command=lambda: start_download_thread(app))
    download_button.pack(pady=10)

    detect_button = ctk.CTkButton(app, text="Detect Data", state='disabled',
                                  command=lambda: open_max_images_id_config(app))
    detect_button.pack(pady=10)

    exit_button = ctk.CTkButton(app, text="Exit", command=lambda: app.destroy())
    exit_button.pack(pady=10)

    app.clear_duplicates = clear_duplicates
    app.load_button = load_button
    app.download_button = download_button
    app.detect_button = detect_button
    app.exit_button = exit_button


def clear_duplicates_thread(app):
    threading.Thread(target=lambda: clear_duplicates_func(app), daemon=True).start()


def clear_duplicates_func(app):
    try:
        app.download_button.configure(state='disabled')

        progress_window = Toplevel(app)
        progress_window.title("Removing Duplicates")
        progress_window.geometry("400x200")

        progress_label = ctk.CTkLabel(progress_window, text="Removing duplicates...", text_color="black")
        progress_label.pack(pady=10)

        progress_bar = ctk.CTkProgressBar(progress_window, width=300, height=20)
        progress_bar.pack(pady=10)
        progress_bar.set(0)

        progress_counter_label = ctk.CTkLabel(progress_window, text="0/0", text_color="black")
        progress_counter_label.pack(pady=10)

        def update_progress(current, total):
            progress = current / total
            progress_bar.set(progress)
            percentage = progress * 100
            progress_counter_label.configure(
                text=f"{percentage:.0f}%"
            )
            progress_window.update_idletasks()

        output_path = "removed_duplicates_" + os.path.basename(app.csv_file_path)
        output_path = os.path.join(os.path.dirname(__file__), output_path)
        remove_duplicates(app.csv_data, output_path, duration_minutes=30, radius_meters=10,
                          update_progress=update_progress)

        app.csv_file_path = output_path
        app.csv_data = handle_csv_file(output_path)
        app.csv_file_path = output_path
        app.download_button.configure(state='normal')

        progress_window.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred during removing duplicates: {e}")


def load_csv_event(app):
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")], initialdir="/", title="Select CSV File")
    if file_path:
        app.csv_data = handle_csv_file(file_path)
        if app.csv_data is not None:
            app.csv_file_path = file_path
            app.download_button.configure(state='normal')
            app.clear_duplicates.configure(state='normal')

            messagebox.showinfo("File Loaded", "CSV data loaded successfully.")
        else:
            messagebox.showerror("Error", "Failed to load CSV data.")
    else:
        messagebox.showinfo("File Selection", "No file selected.")


def start_download_thread(app):
    threading.Thread(target=lambda: download_data_func(app), daemon=True).start()


def download_data_func(app):
    try:
        app.clear_duplicates.configure(state='disabled')
        app.download_button.configure(state='disabled')

        progress_window = Toplevel(app)
        progress_window.title("Downloading Data")
        progress_window.geometry("400x200")

        progress_label = ctk.CTkLabel(progress_window, text="Downloading data...", text_color="black")
        progress_label.pack(pady=10)

        progress_bar = ctk.CTkProgressBar(progress_window, width=300, height=20)
        progress_bar.pack(pady=10)
        progress_bar.set(0)

        progress_counter_label = ctk.CTkLabel(progress_window, text="0/0", text_color="black")
        progress_counter_label.pack(pady=10)

        def update_progress(current, total):
            progress = current / total
            progress_bar.set(progress)
            progress_counter_label.configure(text=f"{current}/{total}")
            progress_window.update_idletasks()

        download_data(app.csv_data, app, app.csv_file_path, update_progress)

        app.detect_button.configure(state='normal')
        messagebox.showinfo("Download Complete", "All images downloaded successfully.")
        progress_window.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred during download: {e}")


def open_max_images_id_config(app):
    top = Toplevel(app)
    top.title("Configure Detection Settings")
    top.geometry("300x200")

    label = ctk.CTkLabel(top, text="Max Images per Category:")
    label.pack(pady=10)

    max_images_var = ctk.StringVar()
    image_count_entry = ctk.CTkEntry(top, textvariable=max_images_var, placeholder_text="Enter number or press MAX")
    image_count_entry.pack(pady=10)

    max_button = ctk.CTkButton(top, text="MAX", command=lambda: max_images_var.set("MAX"))
    max_button.pack(pady=10)

    submit_button = ctk.CTkButton(top, text="Start Detection",
                                  command=lambda: start_detection_thread(app, max_images_var.get(), top))
    submit_button.pack(pady=10)


def start_detection_thread(app, max_images, top):
    threading.Thread(target=lambda: detect_data_func(app, max_images, top), daemon=True).start()


def detect_data_func(app, max_images, top):
    try:
        app.clear_duplicates.configure(state='disabled')
        app.download_button.configure(state='disabled')
        app.detect_button.configure(state='disabled')

        progress_window = Toplevel(app)
        progress_window.title("Detecting Data")
        progress_window.geometry("400x200")

        progress_label = ctk.CTkLabel(progress_window, text="Detecting data...", text_color="black")
        progress_label.pack(pady=10)

        progress_bar = ctk.CTkProgressBar(progress_window, width=300, height=20)
        progress_bar.pack(pady=10)
        progress_bar.set(0)

        progress_counter_label = ctk.CTkLabel(progress_window, text="0/0", text_color="black")
        progress_counter_label.pack(pady=10)

        def update_progress(current, total):
            progress = current / total
            progress_bar.set(progress)
            progress_counter_label.configure(text=f"{current}/{total}")
            progress_window.update_idletasks()

        top.destroy()
        csv_base_name = os.path.splitext(os.path.basename(app.csv_file_path))[0]
        base_directory = os.path.join(current_dir,"..", "data", csv_base_name)
        max_images_per_category = None if max_images.upper() == "MAX" else int(max_images)

        output_directory_name = f"{csv_base_name}_{max_images_per_category if max_images_per_category else 'max'}"
        output_base_directory = os.path.join(current_dir,"..", "output", output_directory_name)

        model = load_model()
        start_time = time.time()

        total_images = sum(min(len(glob.glob(os.path.join(root, dir_name, '*.jpg'))), max_images_per_category) if max_images_per_category is not None else len(glob.glob(os.path.join(root, dir_name, '*.jpg')))
                           for root, dirs, _ in os.walk(base_directory) for dir_name in dirs)

        def update_progress_wrapper(current, total):
            update_progress(current, total)

        process_all_directories(base_directory, model, model.names, output_base_directory, max_images_per_category, update_progress_wrapper)
        output_directory_csv = os.path.join(output_base_directory, 'csv')
        summary_df = process_directory(output_directory_csv)
        summary_file_path = os.path.join(output_base_directory, 'summary_results.csv')
        summary_df.to_csv(summary_file_path, index=False)
        end_time = time.time()
        messagebox.showinfo("Detection Complete",
                            f"Detection process completed successfully in {end_time - start_time:.2f} seconds.")
        progress_window.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred during detection: {e}")
        if 'progress_window' in locals():
            progress_window.destroy()


