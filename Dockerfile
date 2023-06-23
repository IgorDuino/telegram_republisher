FROM python:3.11

LABEL maintainer="me@igorduino.ru"

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["sh", "-c", "aerich init-db && aerich upgrade && python main.py"]