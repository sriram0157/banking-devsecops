FROM python:3.12-alpine3.24

WORKDIR /app

# Upgrade vulnerable Kerberos package
RUN apk update && apk upgrade --no-cache

COPY app/requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip setuptools \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 5000

CMD ["python", "app.py"]