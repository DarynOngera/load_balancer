FROM python:3.8-slim

WORKDIR /app

COPY . .

RUN pip install Flask docker requests --break-system-packages

CMD ["python", "load_balancer.py"]
