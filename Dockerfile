FROM python:3.9-slim-buster

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /app

COPY . /app
RUN apt-get install -y ffmpeg
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
