from PyQt6.QtWidgets import QLabel, QPushButton, QMainWindow, QApplication, QFileDialog
from data import states, time_altered
from requests.exceptions import HTTPError
from PyQt6.QtGui import QFont
import requests
import logging
import sys
import os

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_app()

    def main_app(self):
        self.setWindowTitle("Audio Converter")
        self.setFixedSize(450, 520)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(spread:pad, x1:0, 
                y1:0,x2:0, y2:1, stop:0 #ff7e5f, stop:1 #feb47b);}
            """)

        # Label
        label_font = QFont('Lucida Grande', 30)
        label = QLabel(self)
        label.move(192,80)
        label.setFont(label_font)
        label.setText("MP3")
        label.setStyleSheet("background-color:transparent;")

        # Label
        label_font = QFont('Lucida Grande',10)
        label = QLabel(self)
        label.move(190, 111)
        label.setFont(label_font)
        label.setText("_____________")
        label.setStyleSheet("background-color:transparent;")

        # Label
        label_font = QFont('Lucida Grande', 28)
        label = QLabel(self)
        label.move(190, 150)
        label.setFont(label_font)
        label.setText("WAV")
        label.setStyleSheet("background-color:transparent;")
        
        # Import Button
        btn_font = QFont("Lucida Grande", 20)
        btn = QPushButton(self)
        btn.setText('Import')
        btn.setFont(btn_font)
        btn.move(170, 250)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                stop:0 #ff7e5f, stop:1 #feb47b);
                border: 2px solid #fff;
                border-radius: 10px;
                color: white;
                font-size: 16px;
            }
        """)
        btn.clicked.connect(self.open_file_system)

        # Export Button 
        btn_font = QFont("Lucida Grande", 20)
        btn2 = QPushButton(self)
        btn2.setText('Export')
        btn2.setFont(btn_font)
        btn2.move(170, 300)
        btn2.setStyleSheet("""
            QPushButton {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                stop:0 #ff7e5f, stop:1 #feb47b);
                border: 2px solid #fff;
                border-radius: 10px;
                color: white;
                font-size: 16px;
            }
        """)
        btn2.clicked.connect(self.import_api)
    
    def open_file_system(self):
        try:
            self.file_path, _ = QFileDialog.getOpenFileName(self, "Select an MP3 File", "", "MP3 Files (*.mp3);;All Files (*)")
            if self.file_path:  # Check if a file was selected
                with open(self.file_path, 'rb') as file:  # Open in binary mode
                    content = file.read()  # Read binary content
                    print(f"Successfully read MP3 file: {self.file_path}")
            else:
                print("No file selected.")
        except (FileNotFoundError, FileExistsError) as err:
            logging.error(f'Error opening file: {err}')

    def import_api(self):
        global freeconvert
        freeconvert = requests.Session()
        freeconvert.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {states.api_key}",
        })

        # Create an import/upload task request to the api
        try:
            upload_task_response = freeconvert.post(f"{states.base_url}/process/import/upload") # Store the response in the upload_task_response variable
            upload_task_id = upload_task_response.json()["id"] # Transform that api response into JSON format and extract the id and store it in the upload_task_id variable 
            uploader_form = upload_task_response.json()["result"]["form"] # Take that same upload_task_response and Transform it into JSON, extract the result and form from the api response and store it in the uploader_form variable
            print("Created task", upload_task_id)
        except HTTPError as er:
            logging.error(f'HTTPS Error::{er}')

        # Attach required form parameters and the file
        formdata = {}
        try:
            for key, value in uploader_form["parameters"].items(): # Extract the parameters' key, value pair from the uploader_form and store it the formdata empty dictionary to be used later in a post request to the api
                formdata[key] = value
            files = {'file': open(self.file_path,'rb')}
        except ValueError as e:
            logging.error(f'Error Unpacking Key-Value Pair(s)::{e}')

        # Submit the upload as multipart/form-data request.
        try:
            upload_response = requests.post(uploader_form["url"], files=files, data=formdata)
            upload_response.raise_for_status()
        except HTTPError as err:
            logging.error(f'HTTPS Error: {err}') 

        # Use the uploaded file in a job.
        try:
            job_response = freeconvert.post(f"{states.base_url}/process/jobs", json={
                "tasks": {
                    "myConvert1": {
                        "operation": "convert",
                        "input": upload_task_id,
                        "output_format": "mp3",
                    },
                    "myExport1": {
                        "operation": "export/url",
                        "input": "myConvert1",
                        "filename": f"{states.file_name}.wav",
                    },
                },
            })
        except HTTPError as e_status:
            logging.error(f'HTTPS Error: {e_status}') 

        job = job_response.json()
        print(job_response.json())
        self.wait_for_job_by_polling(job["id"])

        # Fetch the export URL after job completion
        try:
            result_response = freeconvert.get(f"{states.base_url}/process/jobs/")
            result_json = result_response.json()
            save_folder = os.path.join(os.path.expanduser("~"), "Desktop","Misc","Plugin_Folder", "ConvertedFiles")
            os.makedirs(save_folder, exist_ok=True)  # Create folder if it doesn't exist
        except HTTPError as http_err:
            logging.error(http_err)

        try:
            tasks = result_json["tasks"]
            # Iterate through the tasks list to find the task with the "myExport1" name
            for task in tasks:
                if task["name"] == "myExport1":
                    download_url = task["result"]["url"]
                    break
            else:
                raise Exception("Export task 'myExport1' not found")
            local_filename = os.path.join(save_folder, f"{states.file_name}.wav")
            # Download the file locally
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for i in r.iter_content(chunk_size=8192):
                        f.write(i)
            print(f"File downloaded locally as: {local_filename}")
        except KeyError:
            logging.error("Download URL not found in API response.")
            return
            
    def wait_for_job_by_polling(self,job_id):
        for _ in range(10):
            time_altered.time_buffer(2)
            job_get_response = freeconvert.get(f"{states.base_url}/process/jobs/{job_id}")
            job = job_get_response.json()
            if job["status"] == "completed":
                # Using list comprehension to find matching tasks
                export_tasks = [task for task in job["tasks"] if task["name"] == "myExport1"]
                if export_tasks:
                    export_task = export_tasks[0]  # Get the first matching task in the list created by the list comprehension
                    print("Downloadable converted file url:", export_task["result"]["url"])
                    return
                else:
                    raise Exception("Export task not found")
            elif job["status"] == "failed":
                raise Exception("Job failed")
        raise Exception("Poll timeout")
    

def main():
    app = QApplication(sys.argv)
    run = AppWindow()
    run.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()