FROM python:3.11-alpine

RUN apk --no-cache add musl-dev gcc cargo

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "App.py"]