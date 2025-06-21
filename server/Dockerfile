FROM python:3.8-slim

WORKDIR /app

COPY . .

RUN pip install Flask --break-system-packages

CMD ["python", "server.py"]
