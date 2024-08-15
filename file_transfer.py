import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
import subprocess
import os
from datetime import datetime
import threading
import platform

# Determine the platform
current_platform = platform.system()

# Set ADB path based on the platform
if current_platform == "Windows":
    ADB_PATH = os.path.join(os.path.dirname(__file__), "resources", "adb", "windows", "adb.exe")
elif current_platform == "Darwin":  # macOS
    ADB_PATH = os.path.join(os.path.dirname(__file__), "resources", "adb", "macos", "adb")
else:
    raise Exception("Unsupported operating system")

def is_file_transfer_allowed(device_id):
    try:
        result = subprocess.check_output([ADB_PATH, "-s", device_id, "shell", "getprop", "sys.usb.config"])
        return "mtp" in result.decode().lower()
    except subprocess.CalledProcessError:
        return False

def get_device_list():
    try:
        devices = subprocess.check_output([ADB_PATH, "devices"]).decode()
        lines = devices.strip().split('\n')[1:]
        device_list = []
        for line in lines:
            if line.endswith("device"):
                device_id = line.split()[0]
                if is_file_transfer_allowed(device_id):
                    device_list.append(device_id)
        return device_list
    except Exception as e:
        messagebox.showerror("Error", f"Error fetching devices: {str(e)}")
        return []

def update_device_dropdown(device_menu):
    devices = get_device_list()
    device_dropdown.set("----")
    menu = device_menu['menu']
    menu.delete(0, 'end')

    if devices:
        for device in devices:
            menu.add_command(label=device, command=tk._setit(device_dropdown, device))
        device_dropdown.set(devices[0])
        ok_button.config(state=tk.NORMAL)
    else:
        menu.add_command(label="----", state=tk.DISABLED)
        ok_button.config(state=tk.DISABLED)

def show_main_window():
    global root, device_dropdown, ok_button

    root = tk.Tk()
    root.title("Select Device")

    device_dropdown = tk.StringVar(value="----")

    frame = tk.Frame(root)
    frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    tk.Label(frame, text="Select Device:").grid(row=0, column=0, padx=10, pady=10, sticky='e')

    device_menu = tk.OptionMenu(frame, device_dropdown, "----")
    device_menu.grid(row=0, column=1, columnspan=3, padx=10, pady=10, sticky='ew')

    update_button = tk.Button(frame, text="Update Devices", command=lambda: update_device_dropdown(device_menu), width=20)
    update_button.grid(row=1, column=1, padx=10, pady=10, sticky='ew')

    ok_button = tk.Button(frame, text="OK", command=lambda: (root.withdraw(), show_transfer_window()), width=20)
    ok_button.grid(row=1, column=2, padx=10, pady=10, sticky='ew')
    ok_button.config(state=tk.DISABLED)

    root.mainloop()

def show_transfer_window():
    global transfer_window, destination_folder, root, progress_label, progress_bar, percent_label

    transfer_window = tk.Toplevel()
    transfer_window.title("Transfer Files")

    frame = tk.Frame(transfer_window)
    frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    label = tk.Label(frame, text="Select Destination Folder:", width=20, anchor='e')
    label.grid(row=0, column=0, padx=10, pady=10, sticky='e')

    destination_folder = tk.StringVar()
    entry = tk.Entry(frame, textvariable=destination_folder)
    entry.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

    browse_button = tk.Button(frame, text="Browse", command=select_folder, width=12)
    browse_button.grid(row=0, column=4, padx=10, pady=10, sticky="ew")

    transfer_button = tk.Button(frame, text="Transfer Files", command=lambda: start_transfer_thread(destination_folder.get()), width=12)
    transfer_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

    back_button = tk.Button(frame, text="Back", command=lambda: (transfer_window.destroy(), root.deiconify()), width=12)
    back_button.grid(row=1, column=2, padx=10, pady=10, sticky="ew")

    progress_label = tk.Label(frame, text="Progress:")
    progress_label.grid(row=2, column=0, padx=10, pady=10, sticky='e')

    progress_bar = ttk.Progressbar(frame, orient="horizontal", length=400, mode="determinate")
    progress_bar.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky='ew')

    percent_label = tk.Label(frame, text="0%")
    percent_label.grid(row=2, column=4, padx=10, pady=10, sticky='w')

    transfer_window.mainloop()

def start_transfer_thread(destination_folder):
    transfer_thread = threading.Thread(target=transfer_files, args=(destination_folder,))
    transfer_thread.start()

def transfer_files(destination_folder):
    selected_device = device_dropdown.get()
    if not selected_device or selected_device == "----":
        messagebox.showerror("Error", "No device selected")
        return
    
    try:
        new_folder = create_folder(destination_folder)
        
        # Get list of files to transfer
        csv_files = subprocess.check_output([ADB_PATH, "-s", selected_device, "shell", "ls", "/sdcard/Download/*.csv"]).decode().strip().split('\n')
        csv_files = [f for f in csv_files if f]  # Filter out empty results
        txt_files = subprocess.check_output([ADB_PATH, "-s", selected_device, "shell", "ls", "/sdcard/Download/*.txt"]).decode().strip().split('\n')
        txt_files = [f for f in txt_files if f]  # Filter out empty results
        
        files_to_transfer = csv_files + txt_files
        total_files = len(files_to_transfer)
        current_file = 0
        
        # Transfer files
        for file in files_to_transfer:
            file_name = file.split('/')[-1]
            subprocess.run([ADB_PATH, "-s", selected_device, "pull", file, f"{new_folder}/{file_name}"], check=True)
            current_file += 1
            # Update progress in main thread
            transfer_window.after(0, update_progress, current_file, total_files)

        messagebox.showinfo("Success", "Files transferred successfully")
        transfer_window.destroy()
        root.deiconify()
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to transfer files: {e}")
        transfer_window.destroy()
        root.deiconify()

def create_folder(destination_folder):
    folder_name = f"{device_dropdown.get()}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    new_folder = os.path.join(destination_folder, folder_name)
    os.makedirs(new_folder, exist_ok=True)
    return new_folder

def update_progress(current, total):
    if total > 0:
        progress = int((current / total) * 100)
    else:
        progress = 0
    progress_bar['value'] = progress
    percent_label.config(text=f"{progress}%")
    transfer_window.update_idletasks()

def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        destination_folder.set(folder_selected)

if __name__ == "__main__":
    show_main_window()
