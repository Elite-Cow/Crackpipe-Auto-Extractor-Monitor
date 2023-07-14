import os
import time
import zipfile
import tarfile
import importlib
import subprocess
import threading
import sys
import re
import glob
from mainwindow import Ui_window


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
    install_package('watchdog')
    install_package('py7zr')
    install_package('pystray')
    install_package('PyQt5')
    

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
                log.insert(tk.END, f"Extracted {root_folder}")
            elif tarfile.is_tarfile(file_path):
                with tarfile.open(file_path, 'r') as tar_ref:
                    root_folder = os.path.basename(os.path.dirname(file_path))
                    extract_dir = os.path.join(destination_dir, root_folder)
                    tar_ref.extractall(extract_dir)
                log.insert(tk.END, f"Extracted {root_folder}\n")
            elif file_path.endswith('.7z'):
                with py7zr.SevenZipFile(file_path, mode='r') as seven_zip_ref:
                    root_folder = os.path.basename(os.path.dirname(file_path))
                    extract_dir = os.path.join(destination_dir, root_folder)
                    seven_zip_ref.extractall(path=extract_dir)
                log.insert(tk.END, f"Extracted {root_folder}\n")

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

def start_extraction():

    rootpath = None
    appdata = os.getenv('LOCALAPPDATA')
    Filepath = (glob.glob(f'{appdata}\\Packages\\Phalcode.*\\LocalCache\\Roaming\\Crackpipe\\config\\user'))[0]

    pattern = re.compile("RootPath", re.IGNORECASE)  # Compile a case-insensitive regex
    with open (Filepath, 'rt') as config:    
        for line in config:
            if pattern.search(line) != None:      # If a match is found 
                rootpath =line.split('RootPath=',1)[1].rstrip('\n')

    source_dir = rootpath + "Crackpipe\\Downloads"
    destination_dir = rootpath + "Crackpipe\\Installations"
    # destination_dir = rootpath + "Crackpipe\\Downloads"

    if not source_dir or not destination_dir:
        ui.log.insertPlainText(f"Source and destination directories could not be found.\n")
        return

    ui.log.insertPlainText(f"Monitoring source directory: {source_dir}\n")
    ui.log.insertPlainText(f"Destination directory: {destination_dir}\n")

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
                self.log.insertPlainText(f"New file detected: {event.src_path}\n")
                thread = threading.Thread(target=extract_compressed_file,
                                          args=(event.src_path, self.destination_dir, self.log))
                thread.start()

    event_handler = FileHandler(source_dir, destination_dir, ui.log)
    observer = Observer()
    observer.schedule(event_handler, path=source_dir, recursive=True)
    observer.start()

# Install dependencies
install_dependencies()

#import installed dependecies
import py7zr
from PyQt5 import QtCore, QtGui, QtWidgets

app = QtWidgets.QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

MainWindow = QtWidgets.QMainWindow() 
ui = Ui_window()
ui.setupUi(MainWindow)
# MainWindow.show()

icon= QtGui.QIcon('C:/users/dillo/downloads/icon.ico')
tray = QtWidgets.QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

show = QtWidgets.QAction("Open Crackpipe Auto Extractor")
show.triggered.connect(lambda: MainWindow.show())
quit = QtWidgets.QAction("Quit")
quit.triggered.connect(app.quit)

menu = QtWidgets.QMenu()
menu.addAction(show)
menu.addAction(quit)

tray.setContextMenu(menu)

start_extraction()

sys.exit(app.exec_())