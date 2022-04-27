FROM python:3.11-rc-alpine
ENV LANG C.UTF-8

RUN mkdir /django

RUN apk update
RUN apk add postgresql-dev postgresql-client gcc  musl-dev
# RUN apt-get install -y python python-pip python-dev python-psycopg2 postgresql-client 

ADD requirements.txt /django/requirements.txt
RUN pip install -r /django/requirements.txt

WORKDIR /django

EXPOSE 8000

CMD gunicorn -b :8000 django.wsgi