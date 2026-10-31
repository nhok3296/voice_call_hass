ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.20
FROM ${BUILD_FROM}

# Cài đặt FFmpeg và tzdata
RUN apk add --no-cache \
    ffmpeg \
    tzdata

WORKDIR /app

# Cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn ứng dụng
COPY app /app/app
COPY web /app/web
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

EXPOSE 8099 8098

CMD [ "/app/run.sh" ]

