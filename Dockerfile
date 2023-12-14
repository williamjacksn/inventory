FROM python:3.11.0-alpine3.15

RUN /sbin/apk add --no-cache libpq
RUN /usr/sbin/adduser -g python -D python

USER python
RUN /usr/local/bin/python -m venv /home/python/venv
WORKDIR /home/python/inventory

COPY --chown=python:python requirements.txt /home/python/inventory/requirements.txt
RUN /home/python/venv/bin/pip install --no-cache-dir --requirement /home/python/inventory/requirements.txt

ENV APP_VERSION="2021.1" \
    PATH="/home/python/venv/bin:${PATH}" \
    PYTHONUNBUFFERED="1"

ENTRYPOINT ["/home/python/venv/bin/python"]
CMD ["/home/python/inventory/run.py"]
HEALTHCHECK CMD ["/usr/bin/wget", "--spider", "--quiet", "localhost:8080"]

LABEL org.opencontainers.image.authors="William Jackson <william@subtlecoolness.com>" \
      org.opencontainers.image.source="https://github.com/williamjacksn/inventory" \
      org.opencontainers.image.version="${APP_VERSION}"

COPY --chown=python:python run.py /home/python/inventory/run.py
COPY --chown=python:python inventory /home/python/inventory/inventory
