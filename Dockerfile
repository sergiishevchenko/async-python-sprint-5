FROM python:3.11-slim

COPY . /code

WORKDIR /code

RUN apt-get update
RUN apt-get -y install gcc

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt