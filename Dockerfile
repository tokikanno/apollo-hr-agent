FROM python:3.11-slim

ENV TZ="Asia/Taipei"

COPY requirements.txt .

RUN pip install -r requirements.txt \
    && rm requirements.txt
