FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE ${PORT:-8080}

CMD gunicorn --bind 0.0.0.0:${PORT:-8080} app:app
