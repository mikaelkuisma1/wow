FROM python:3.13-slim AS base

WORKDIR /work

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM base AS wow

COPY wow /work/wow
COPY scripts /work/scripts
RUN pip install /work/wow 

RUN mkdir outputs && cd outputs && python ../scripts/run_workflow.py
