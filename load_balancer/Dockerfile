FROM python:3.11-slim

WORKDIR /app

COPY src/ src/
COPY pyproject.toml .

RUN pip install . --break-system-packages

CMD ["python", "-m", "load_balancer"]
