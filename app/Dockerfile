FROM python:3.9

COPY requirements.txt /app/requirements.txt
COPY src /app

WORKDIR /app

RUN apt-get update && apt-get install -y libgl1-mesa-glx tesseract-ocr
RUN apt-get install -y wget && \ 
    wget https://github.com/tesseract-ocr/tessdata/raw/main/rus.traineddata -P /usr/share/tesseract-ocr/5/tessdata/

RUN pip install -r requirements.txt

CMD ["python", "app.py"]