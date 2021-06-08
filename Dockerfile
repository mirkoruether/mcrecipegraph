FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn

COPY . .

CMD ["gunicorn"  , "-b", "0.0.0.0:8080", "main:app"]
