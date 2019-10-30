FROM python:3.6-alpine
LABEL maintainer="ach@dvhb.ru"

RUN apk add --update \
    build-base gcc \
    libffi-dev openssl-dev \
    linux-headers \
    && rm -rf /var/cache/apk/*

WORKDIR /app
COPY requirements.txt /app

RUN pip install pip --upgrade && \
    pip install -r requirements.txt
COPY . /app

CMD python -m run 
