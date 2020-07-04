FROM python:3.8.3-alpine3.12

COPY requirements.txt /inventory/requirements.txt

RUN /sbin/apk add --no-cache --virtual .deps gcc musl-dev postgresql-dev \
 && /sbin/apk add --no-cache libpq \
 && /usr/local/bin/pip install --no-cache-dir --requirement /inventory/requirements.txt \
 && /sbin/apk del --no-cache .deps

COPY . /inventory

ENV APP_VERSION="2020.3" \
    PYTHONUNBUFFERED="1"

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/inventory/run.py"]
HEALTHCHECK CMD ["/usr/bin/wget", "--spider", "--quiet", "localhost:8080"]

LABEL org.opencontainers.image.authors="William Jackson <william@subtlecoolness.com>" \
      org.opencontainers.image.source="https://github.com/williamjacksn/inventory" \
      org.opencontainers.image.version="${APP_VERSION}"
