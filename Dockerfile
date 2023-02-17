FROM python:alpine3.16

WORKDIR /usr/src/app

COPY usdx_scraper.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python", "usdx_scraper.py"]

# docker run -v ${PWD}/docker_input:/data -it usdx_scraper ...
