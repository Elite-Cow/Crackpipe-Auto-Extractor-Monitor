import os
import time
import zipfile
import tarfile
import py7zr
import importlib
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def install_package(package_name):
    try:
        importlib.import_module(package_name)
    except ImportError:
        subprocess.check_call(['pip', 'install', package_name])

def install_dependencies():
    install_package('tkinter')
    install_package('watchdog')
    install_package('py7zr')

def extract_compressed_file(file_path, destination_dir, log):
    max_retries = 360
    retry_delay = 5  # in seconds
    retries = 0

    while retries < max_retries:
        try:
            if zipfile.is_zipfile(file_path):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    root_folder = os.path.basename(os.path.dirname(file_path))
                    extract_dir = os.path.join(destination_dir, root_folder)
                    zip_ref.extractall(extract_dir)
                log.insert(tk.END, f"Extracted {root_folder} to {extract_dir}")
            elif tarfile.is_tarfile(file_path):
                with tarfile.open(file_path, 'r') as tar_ref:
                    root_folder = os.path.basename(os.path.dirname(file_path))
                    extract_dir = os.path.join(destination_dir, root_folder)
                    tar_ref.extractall(extract_dir)
                log.insert(tk.END, f"Extracted {root_folder} to {extract_dir}\n")
            elif file_path.endswith('.7z'):
                with py7zr.SevenZipFile(file_path, mode='r') as seven_zip_ref:
                    root_folder = os.path.basename(os.path.dirname(file_path))
                    extract_dir = os.path.join(destination_dir, root_folder)
                    seven_zip_ref.extractall(path=extract_dir)
                log.insert(tk.END, f"Extracted {root_folder} to {extract_dir}\n")

            # Extraction successful, break out of the loop
            break
        
        except FileNotFoundError:
            pass

        except PermissionError:
            # File is locked, wait and retry after delay
            retries += 1
            #log.insert(tk.END, f"PermissionError: [Errno 13] Permission denied. Retry {retries}/{max_retries}\n")
            time.sleep(retry_delay)

    if retries >= max_retries:
        log.insert(tk.END, f"Extraction failed after {max_retries} retries. File may still be locked.\n")

def select_source_dir():
    source_dir = filedialog.askdirectory()
    source_entry.delete(0, tk.END)
    source_entry.insert(tk.END, source_dir)

def select_destination_dir():
    destination_dir = filedialog.askdirectory()
    destination_entry.delete(0, tk.END)
    destination_entry.insert(tk.END, destination_dir)

def start_extraction():
    source_dir = source_entry.get()
    destination_dir = destination_entry.get()

    if not source_dir or not destination_dir:
        log.insert(tk.END, "Please select source and destination directories.\n")
        return

    log.insert(tk.END, f"Monitoring source directory: {source_dir}\n")
    log.insert(tk.END, f"Destination directory: {destination_dir}\n")

    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    class FileHandler(FileSystemEventHandler):
        def __init__(self, source_dir, destination_dir, log):
            super().__init__()
            self.source_dir = source_dir
            self.destination_dir = destination_dir
            self.log = log

        def on_created(self, event):
            if not event.is_directory:
                self.log.insert(tk.END, f"New file detected: {event.src_path}\n")
                thread = threading.Thread(target=extract_compressed_file,
                                          args=(event.src_path, self.destination_dir, self.log))
                thread.start()

    event_handler = FileHandler(source_dir, destination_dir, log)
    observer = Observer()
    observer.schedule(event_handler, path=source_dir, recursive=True)
    observer.start()

# Install dependencies
install_dependencies()

# Create the main window
window = tk.Tk()
window.title("Crackpipe Auto Extractor")
window.geometry("600x400")
# Set the application icon
#window.wm_attributes('-toolwindow', 'True')
window.iconbitmap(sys._MEIPASS + '\icon.ico')

# Source Directory
source_label = tk.Label(window, text="Crackpipe Downloads Directory:")
source_label.pack()
source_entry = tk.Entry(window, width=60)
source_entry.pack(side=tk.TOP)
source_button = tk.Button(window, text="Browse", command=select_source_dir)
source_button.pack(side=tk.TOP)

# Destination Directory
destination_label = tk.Label(window, text="Crackpipe Installations Directory:")
destination_label.pack()
destination_entry = tk.Entry(window, width=60)
destination_entry.pack(side=tk.TOP)
destination_button = tk.Button(window, text="Browse", command=select_destination_dir)
destination_button.pack(side=tk.TOP)

# Output Log
log_label = tk.Label(window, text="Process Log:")
log_label.pack()
log = scrolledtext.ScrolledText(window, height=10, width=70)
log.pack()

# Start Extraction Button
start_button = tk.Button(window, text="Start Monitoring", command=start_extraction, pady=15,)
start_button.pack(pady=15)

# Run the GUI main loop
window.mainloop()
