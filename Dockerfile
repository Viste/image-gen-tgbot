FROM python:3.9-slim-buster

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /app

COPY . /app
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:mc3man/trusty-media
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
