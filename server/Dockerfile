FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install Flask --break-system-packages

CMD ["python", "app.py"]
