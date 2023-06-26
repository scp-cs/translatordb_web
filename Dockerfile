FROM python:3.11-alpine

RUN apk --no-cache add musl-dev gcc cargo

WORKDIR /app

COPY requirements.txt /app

# Installing bcrypt in a separate step speeds up the build by A LOT
RUN pip install --no-cache-dir bcrypt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8080

CMD ["python", "App.py"]