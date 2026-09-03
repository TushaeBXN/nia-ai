FROM runpod/base:0.6.2-cuda12.1.0

ENV PYTHONUNBUFFERED=1
ENV NIA_SHARED_DIR=/tmp/nia-shared
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cached layer)
COPY deploy/runpod/requirements.txt ./requirements_runpod.txt
RUN pip3 install --no-cache-dir -r requirements_runpod.txt

# Copy only what the handler needs
COPY agents/ ./agents/
COPY nia/ ./nia/
COPY knowledge/ ./knowledge/
COPY coordination/ ./coordination/

COPY deploy/runpod/handler.py ./handler.py

CMD ["python3", "-u", "/app/handler.py"]
