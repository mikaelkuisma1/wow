FROM python:3.13-slim

WORKDIR /work

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
COPY requirements.txt .

RUN pip install -r requirements.txt

RUN mkdir wow && cd wow && tb init
