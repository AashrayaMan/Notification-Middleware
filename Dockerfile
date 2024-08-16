FROM python:3.10.9-slim-bullseye

WORKDIR /app
COPY requirements.txt /app

RUN pip3 install -r requirements.txt
COPY . /app

CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8585"]
