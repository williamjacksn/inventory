FROM python:3.7.0-alpine3.8

COPY requirements.txt /inventory/requirements.txt

RUN apk --no-cache add --virtual .deps gcc musl-dev postgresql-dev \
 && apk --no-cache add libpq \
 && /usr/local/bin/pip install --no-cache-dir --upgrade pip setuptools \
 && /usr/local/bin/pip install --no-cache-dir --requirement /inventory/requirements.txt \
 && apk del .deps

COPY . /inventory

ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/inventory/run.py"]
