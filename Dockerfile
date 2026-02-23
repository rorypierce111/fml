FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# IMPORTANT: remove EXPOSE 5000
# OR change it to 8080 for clarity
EXPOSE 8080

CMD gunicorn -b 0.0.0.0:$PORT app:app