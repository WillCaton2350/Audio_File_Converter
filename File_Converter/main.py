from PyQt6.QtWidgets import QLabel, QPushButton, QMainWindow, QApplication
from conversion_API.data import states
from PyQt6.QtGui import QFont
import requests
import sys
import time

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_app()

    def main_app(self):
        self.setFixedSize(450, 750)

        # Label
        label_font = QFont('Arial', 40)
        label = QLabel(self)
        label.move(175, 50)
        label.setFont(label_font)
        label.setText("Main")

        # Button
        btn_font = QFont("Arial", 20)
        btn = QPushButton(self)
        btn.setText('Execute')
        btn.setFont(btn_font)
        btn.move(170, 100)
        btn.clicked.connect(self.import_api)

    def import_api(self):
        global freeconvert
        freeconvert = requests.Session()
        freeconvert.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {states.api_key}",
        })

        # Create an import/upload task
        upload_task_response = freeconvert.post(f"{states.base_url}/process/import/upload")
        upload_task_id = upload_task_response.json()["id"]
        uploader_form = upload_task_response.json()["result"]["form"]
        print("Created task", upload_task_id)

        # Attach required form parameters and the file
        formdata = {}
        for parameter, value in uploader_form["parameters"].items():
            formdata[parameter] = value
        files = {'file': open(states.upload_file_path,'rb')}

        # Submit the upload as multipart/form-data request.
        upload_response = requests.post(uploader_form["url"], files=files, data=formdata)
        upload_response.raise_for_status()

        # Use the uploaded file in a job.
        # Job will complete when all its children and dependent tasks are complete.
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
                    "filename": "my-converted-file.wav",
                },
            },
        })
        job = job_response.json()
        self.wait_for_job_by_polling(job["id"])

    
    def wait_for_job_by_polling(self,job_id):
        for _ in range(10):
            time.sleep(2)
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
