import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import subprocess
import os
from datetime import datetime
import threading
import platform

# ตรวจสอบระบบปฏิบัติการ
current_platform = platform.system()

# ตั้งค่า ADB path ตามระบบปฏิบัติการ
if current_platform == "Windows":
    ADB_PATH = os.path.join(os.path.dirname(__file__), "resources", "adb", "windows", "adb.exe")
elif current_platform == "Darwin":  # macOS
    ADB_PATH = os.path.join(os.path.dirname(__file__), "resources", "adb", "macos", "adb")
else:
    raise Exception("ระบบปฏิบัติการไม่รองรับ")

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
        messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการดึงอุปกรณ์: {str(e)}")
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
    root.title("เลือกอุปกรณ์")

    device_dropdown = tk.StringVar(value="----")

    frame = tk.Frame(root)
    frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    tk.Label(frame, text="เลือกอุปกรณ์:").grid(row=0, column=0, padx=10, pady=10, sticky='e')

    device_menu = tk.OptionMenu(frame, device_dropdown, "----")
    device_menu.grid(row=0, column=1, columnspan=3, padx=10, pady=10, sticky='ew')

    update_button = tk.Button(frame, text="อัปเดตอุปกรณ์", command=lambda: update_device_dropdown(device_menu), width=20)
    update_button.grid(row=1, column=1, padx=10, pady=10, sticky='ew')

    ok_button = tk.Button(frame, text="ตกลง", command=lambda: update_and_proceed(device_menu), width=20)
    ok_button.grid(row=1, column=2, padx=10, pady=10, sticky='ew')
    ok_button.config(state=tk.DISABLED)

    root.mainloop()

def update_and_proceed(device_menu):
    update_device_dropdown(device_menu)
    if device_dropdown.get() == "----":
        messagebox.showwarning("ไม่มีอุปกรณ์", "โปรดอัปเดตอุปกรณ์และลองอีกครั้ง")
    else:
        root.withdraw()
        show_transfer_window()

def get_download_folder_on_device(device_id):
    try:
        result = subprocess.check_output([ADB_PATH, "-s", device_id, "shell", "echo", "$EXTERNAL_STORAGE/Download"])
        download_folder = result.decode().strip()
        return download_folder
    except subprocess.CalledProcessError:
        return None

def show_transfer_window():
    global transfer_window, destination_folder, root, progress_label, progress_bar, percent_label

    # Determine the default download folder based on the operating system
    if current_platform == "Windows":
        default_download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    elif current_platform == "Darwin":  # macOS
        default_download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    else:
        default_download_path = os.path.expanduser("~")  # Fallback to home directory for other platforms

    transfer_window = tk.Toplevel()
    transfer_window.title("ถ่ายโอนข้อมูล")

    frame = tk.Frame(transfer_window)
    frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    font = ("TH Sarabun", 12)

    destination_folder = tk.StringVar(value=default_download_path)

    label = tk.Label(frame, text="เลือกโฟลเดอร์ปลายทาง:", width=20, anchor='e', font=font)
    label.grid(row=0, column=0, padx=10, pady=10, sticky='e')

    entry = tk.Entry(frame, textvariable=destination_folder, font=font)
    entry.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

    browse_button = tk.Button(frame, text="เรียกดู", command=select_folder, width=12, font=font)
    browse_button.grid(row=0, column=4, padx=10, pady=10, sticky="ew")

    transfer_button = tk.Button(frame, text="ถ่ายโอนข้อมูล", command=lambda: start_transfer_thread(destination_folder.get()), width=12, font=font)
    transfer_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

    back_button = tk.Button(frame, text="ย้อนกลับ", command=lambda: (transfer_window.destroy(), root.deiconify()), width=12, font=font)
    back_button.grid(row=1, column=2, padx=10, pady=10, sticky="ew")

    progress_label = tk.Label(frame, text="ความก้าวหน้า:", font=font)
    progress_label.grid(row=2, column=0, padx=10, pady=10, sticky='e')

    progress_bar = ttk.Progressbar(frame, orient="horizontal", length=400, mode="determinate")
    progress_bar.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky='ew')

    percent_label = tk.Label(frame, text="0%", font=font)
    percent_label.grid(row=2, column=4, padx=10, pady=10, sticky='w')

    transfer_window.mainloop()

def start_transfer_thread(destination_folder):
    transfer_thread = threading.Thread(target=transfer_files, args=(destination_folder,))
    transfer_thread.start()

def transfer_files(destination_folder):
    selected_device = device_dropdown.get()
    if not selected_device or selected_device == "----":
        messagebox.showerror("ข้อผิดพลาด", "ไม่มีการเลือกอุปกรณ์")
        return

    try:
        new_folder = create_folder(destination_folder)
        
        # ดึงรายการไฟล์ที่จะถ่ายโอน
        try:
            csv_files = subprocess.check_output([ADB_PATH, "-s", selected_device, "shell", "ls", "/sdcard/Download/*.csv"]).decode().strip().split('\n')
            csv_files = [f for f in csv_files if f]
            txt_files = subprocess.check_output([ADB_PATH, "-s", selected_device, "shell", "ls", "/sdcard/Download/*.txt"]).decode().strip().split('\n')
            txt_files = [f for f in txt_files if f]
        except subprocess.CalledProcessError as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถดึงรายการไฟล์ได้: {str(e)}")
            return
        
        files_to_transfer = csv_files + txt_files
        total_files = len(files_to_transfer)
        current_file = 0
        
        # ถ่ายโอนไฟล์
        for file in files_to_transfer:
            file_name = file.split('/')[-1]
            try:
                subprocess.run([ADB_PATH, "-s", selected_device, "pull", file, f"{new_folder}/{file_name}"], check=True)
            except subprocess.CalledProcessError as e:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถถ่ายโอนไฟล์ {file_name} ได้: {str(e)}")
                continue
            
            current_file += 1
            
            # อัปเดต UI
            progress = (current_file / total_files) * 100
            progress_bar['value'] = progress
            percent_label.config(text=f"{int(progress)}%")
            transfer_window.update_idletasks()
        
        messagebox.showinfo("สำเร็จ", "การถ่ายโอนข้อมูลเสร็จสิ้น")
        transfer_window.destroy()
        root.deiconify()  # แสดงหน้าแรกอีกครั้ง

    except Exception as e:
        messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {str(e)}")

def create_folder(destination_folder):
    now = datetime.now()
    folder_name = now.strftime("%Y-%m-%d_%H-%M-%S")
    new_folder = os.path.join(destination_folder, folder_name)
    os.makedirs(new_folder, exist_ok=True)
    return new_folder

def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        destination_folder.set(folder)

show_main_window()
