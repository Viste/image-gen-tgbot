FROM python:3.9-slim-buster

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /app

COPY . /app
RUN apt-get update && apt-get install -y ffmpeg python3-pyaudio libportaudio2
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
