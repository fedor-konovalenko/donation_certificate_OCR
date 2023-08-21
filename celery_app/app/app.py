from fastapi import FastAPI, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse
import uvicorn
import argparse
import os
import logging
from celery import Celery
from celery.signals import setup_logging
from model import recognize_image

app = FastAPI()
celery_app = Celery("worker", broker="redis://redis:6379/0",
                    backend="redis://redis")
celery_app.conf.update({'worker_hijack_root_logger': False})
#logging.basicConfig(filename="py_log.log",filemode="w", \
                    #format="%(asctime)s %(levelname)s %(message)s")

app_logger = logging.getLogger(__name__)
app_logger.setLevel(logging.INFO)
app_handler = logging.StreamHandler()#FileHandler(f"{__name__}.log", mode='w')
app_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
app_handler.setFormatter(app_formatter)
app_logger.addHandler(app_handler)    
    
@app.get("/health")
def health():
    return {"status": "OK"}

@app.get("/")
def main():
    html_content = """
            <body>
            <form action="/ocr" enctype="multipart/form-data" method="post">
            <input name="file" type="file">
            <input type="submit">
            </form>
            </body>
            """
    return HTMLResponse(content=html_content)

@app.post("/ocr")
def process_request(file: UploadFile):
    task = process_file.delay(file.file.read())
    logging.info(f"Task {task.id} sent to Celery")
    return {"task_id": task.id}

@app.get("/result/{task_id}")
def get_result(task_id: str):
    task = celery_app.AsyncResult(task_id)
    if task.state == "SUCCESS":
        logging.info(f"Task {task_id} completed successfully")
        return task.result
    else:
        logging.warning(
            f"Task {task_id} is not completed yet, current state: {task.state}")
        return {"status": task.state}


@celery_app.task(name="process_file")

def process_file(file_content: bytes):
    try:
        save_pth = os.path.join(os.path.dirname(__file__), "tmp", "image")
        app_logger.info(f'processing file {save_pth}')
        with open(save_pth, "wb") as fid:
            fid.write(file_content)

        res, status, csv_path = recognize_image(save_pth)
        if 'Изображение распознано' in status:
            app_logger.info(f'processing status {status}')
            return {"filename": save_pth, "status": status, "info": res}
        else:
            app_logger.warning(f'some problems {status}')
            return {"filename": save_pth, "status": status}
        
    except Exception as e:
        logging.error(f"Error while processing file: {e}")
        raise e
           

    

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--port", default=8000, type=int, dest="port")
#     parser.add_argument("--host", default="0.0.0.0", type=str, dest="host")
#     args = vars(parser.parse_args())

# uvicorn.run(app, **args)