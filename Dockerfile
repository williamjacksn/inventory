FROM python:3.9.3-alpine3.13

COPY requirements.txt /inventory/requirements.txt

RUN /sbin/apk add --no-cache libpq
RUN /usr/local/bin/pip install --no-cache-dir --requirement /inventory/requirements.txt

COPY . /inventory

ENV APP_VERSION="2021.1" \
    PYTHONUNBUFFERED="1"

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/inventory/run.py"]
HEALTHCHECK CMD ["/usr/bin/wget", "--spider", "--quiet", "localhost:8080"]

LABEL org.opencontainers.image.authors="William Jackson <william@subtlecoolness.com>" \
      org.opencontainers.image.source="https://github.com/williamjacksn/inventory" \
      org.opencontainers.image.version="${APP_VERSION}"

USER nobody
