FROM python:3.7.1-alpine3.8

COPY requirements.txt /inventory/requirements.txt

RUN /sbin/apk add --no-cache --virtual .deps gcc musl-dev postgresql-dev \
 && /sbin/apk add --no-cache libpq \
 && /usr/local/bin/pip install --no-cache-dir --requirement /inventory/requirements.txt \
 && /sbin/apk del --no-cache .deps

COPY . /inventory

ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/inventory/run.py"]

LABEL maintainer=william@subtlecoolness.com \
      org.label-schema.schema-version=1.0 \
      org.label-schema.version=3.0.2
