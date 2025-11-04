FROM python:3-alpine

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apk add --no-cache ffmpeg

COPY usdx_scraper.py .
COPY src/ src/

ENTRYPOINT [ "python", "usdx_scraper.py"]
