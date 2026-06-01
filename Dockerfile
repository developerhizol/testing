FROM python:3.11-slim

RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p /app/configs

EXPOSE 9174

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
