FROM python:3.7.0-alpine3.8

EXPOSE 8080

COPY requirements.txt /app/requirements.txt

RUN apk --no-cache add --virtual .deps gcc musl-dev postgresql-dev \
 && apk --no-cache add libpq \
 && /usr/local/bin/pip install --no-cache-dir --upgrade pip setuptools \
 && /usr/local/bin/pip install --no-cache-dir --requirement /app/requirements.txt \
 && apk del .deps

COPY . /app

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/app/run.py"]