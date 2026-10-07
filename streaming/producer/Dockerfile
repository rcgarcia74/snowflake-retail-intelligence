FROM python:3.13-slim

WORKDIR /app

COPY streaming/producer/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY streaming/producer/produce.py /app/streaming/producer/produce.py

ENTRYPOINT ["python", "/app/streaming/producer/produce.py"]
