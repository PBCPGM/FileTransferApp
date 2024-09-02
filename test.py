import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import subprocess
import os
from datetime import datetime

# ตัวแปร global
selected_path = os.path.expanduser('~/Downloads')  # กำหนด path เริ่มต้น
device_connected = False
root = None  # ประกาศตัวแปร global

def check_device_connection():
    global device_connected, root
    try:
        result = subprocess.check_output(["adb", "devices"]).decode()
        devices = result.strip().split('\n')[1:]  # เอาเฉพาะรายชื่ออุปกรณ์ที่เชื่อมต่อ
        
        # ตรวจสอบว่ามีอุปกรณ์ที่เชื่อมต่ออยู่
        device_connected = any('device' in device for device in devices)
        
        if device_connected:
            # ตรวจสอบว่าอุปกรณ์อนุญาตให้ถ่ายโอนไฟล์ได้หรือไม่
            # ทำการดึงสถานะการอนุญาต
            status_result = subprocess.check_output(["adb", "shell", "pm", "list", "packages"]).decode()
            # ถ้าไม่พบอุปกรณ์หรือไม่มีสถานะอนุญาต
            if "package:" not in status_result:
                messagebox.showerror("ข้อผิดพลาด", "อุปกรณ์ไม่ได้รับอนุญาตให้ถ่ายโอนไฟล์")
                transfer_button.config(state=tk.DISABLED)  # Disable transfer button
            else:
                messagebox.showinfo("ข้อมูล", "อุปกรณ์เชื่อมต่อแล้วและอนุญาตให้ถ่ายโอน")
                transfer_button.config(state=tk.NORMAL)  # Enable transfer button
        else:
            messagebox.showerror("ข้อผิดพลาด", "ไม่พบอุปกรณ์")
            transfer_button.config(state=tk.DISABLED)  # Disable transfer button
    except subprocess.CalledProcessError as e:
        messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถตรวจสอบอุปกรณ์ได้: {e}")

def select_path_on_device():
    global selected_path
    new_path = filedialog.askdirectory(initialdir=selected_path)
    if new_path:
        selected_path = new_path
        path_label.config(text=f"เส้นทางที่เลือก: {selected_path}")

def create_folder_on_device():
    if not selected_path:
        messagebox.showerror("ข้อผิดพลาด", "กรุณาเลือกเส้นทางก่อน")
        return None
    
    # ตรวจสอบไฟล์ก่อนสร้างโฟลเดอร์
    if not check_files_on_device():
        messagebox.showinfo("ข้อมูล", "ไม่พบไฟล์ .csv หรือ .txt บนอุปกรณ์")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    device_name = get_device_name()
    folder_name = f"{device_name}_{timestamp}"
    full_path = os.path.join(selected_path, folder_name)
    
    try:
        # ตรวจสอบและสร้างโฟลเดอร์ใน Windows
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        
        device_folder_path = f"/storage/emulated/0/{folder_name}"  # ปรับ path ตามอุปกรณ์ของคุณ
        subprocess.run(["adb", "shell", "mkdir", "-p", device_folder_path], check=True)
        messagebox.showinfo("สำเร็จ", f"สร้างโฟลเดอร์แล้ว: {device_folder_path}")
        return full_path
    except subprocess.CalledProcessError as e:
        messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถสร้างโฟลเดอร์ได้: {e}")
        return None

def check_files_on_device():
    """ ตรวจสอบว่าอุปกรณ์มีไฟล์ .csv หรือ .txt หรือไม่ """
    try:
        # ค้นหาไฟล์ .csv และ .txt บนอุปกรณ์
        files = subprocess.check_output(["adb", "shell", "find", "/storage/emulated/0/Download", "-name", "*.csv", "-o", "-name", "*.txt"]).decode().splitlines()

        if not files:
            return False
        
        return True
    except subprocess.CalledProcessError as e:
        messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถตรวจสอบไฟล์ได้: {e}")
        return False

def create_folder_on_device():
    if not selected_path:
        messagebox.showerror("ข้อผิดพลาด", "กรุณาเลือกเส้นทางก่อน")
        return None
    
    # ตรวจสอบไฟล์ก่อนสร้างโฟลเดอร์
    if not check_files_on_device():
        messagebox.showinfo("ข้อมูล", "ไม่พบไฟล์ .csv หรือ .txt บนอุปกรณ์")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    device_name = get_device_name()
    folder_name = f"{device_name}_{timestamp}"
    full_path = os.path.join(selected_path, folder_name)
    
    try:
        # ตรวจสอบและสร้างโฟลเดอร์ใน Windows
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        
        device_folder_path = f"/storage/emulated/0/{folder_name}"  # ปรับ path ตามอุปกรณ์ของคุณ
        subprocess.run(["adb", "shell", "mkdir", "-p", device_folder_path], check=True)
        messagebox.showinfo("สำเร็จ", f"สร้างโฟลเดอร์แล้ว: {device_folder_path}")
        return full_path
    except subprocess.CalledProcessError as e:
        messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถสร้างโฟลเดอร์ได้: {e}")
        return None

def get_device_name():
    try:
        result = subprocess.check_output(["adb", "shell", "getprop", "ro.product.model"]).decode().strip()
        return result if result else "device"
    except subprocess.CalledProcessError:
        return "device"

def download_files_from_device(folder_path):
    global root, progress_bar, status_label
    if not folder_path:
        # ไม่ต้องตรวจสอบเส้นทางอีกแล้ว
        return
    
    try:
        # ค้นหาไฟล์ .csv และ .txt บนอุปกรณ์
        files = subprocess.check_output(["adb", "shell", "find", "/storage/emulated/0/Download", "-name", "*.csv", "-o", "-name", "*.txt"]).decode().splitlines()

        if not files:
            messagebox.showinfo("ข้อมูล", "ไม่พบไฟล์ .csv หรือ .txt")
            return
        
        total_files = len(files)
        
        progress_bar['value'] = 0
        progress_bar['maximum'] = total_files
        status_label.config(text="กำลังดาวน์โหลดไฟล์...")
        root.update_idletasks()  # อัปเดต UI
        
        for i, file in enumerate(files):
            file_name = os.path.basename(file)
            destination_path = os.path.join(folder_path, file_name)
            subprocess.run(["adb", "pull", file, destination_path], check=True)
            progress_bar['value'] = i + 1
            status_label.config(text=f"ดาวน์โหลดไฟล์ {i + 1}/{total_files} เสร็จสิ้น")
            root.update_idletasks()  # อัปเดต UI
        
        messagebox.showinfo("สำเร็จ", "ดาวน์โหลดไฟล์เสร็จสิ้น")
        status_label.config(text="ดาวน์โหลดเสร็จสิ้น")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถดาวน์โหลดไฟล์ได้: {e}")

def create_ui():
    global path_label, transfer_button, progress_bar, status_label, root
    
    root = tk.Tk()
    root.title("จัดการไฟล์ ADB")
    
    # ปุ่ม "Update"
    tk.Button(root, text="ตรวจสอบการเชื่อมต่ออุปกรณ์", command=check_device_connection).pack(pady=10)
    
    # ปุ่ม "เลือกเส้นทาง"
    tk.Label(root, text="เลือกเส้นทางบนเครื่อง:").pack(pady=10)
    tk.Button(root, text="เลือกเส้นทาง", command=select_path_on_device).pack(pady=5)
    
    path_label = tk.Label(root, text=f"เส้นทางที่เลือก: {selected_path}")
    path_label.pack(pady=10)
    
    # ปุ่ม "ย้ายไฟล์"
    transfer_button = tk.Button(root, text="สร้างโฟลเดอร์และย้ายไฟล์", command=lambda: download_files_from_device(create_folder_on_device()), state=tk.DISABLED)
    transfer_button.pack(pady=20)
    
    # Progress Bar และ Status Label
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    progress_bar.pack(pady=10)
    
    status_label = tk.Label(root, text="")
    status_label.pack(pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    create_ui()
