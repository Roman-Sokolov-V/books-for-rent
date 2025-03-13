FROM python:3.12.9-alpine3.21

LABEL maintainer="gnonasis@gmail.com"

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .
