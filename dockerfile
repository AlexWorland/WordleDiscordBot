FROM python:latest
ENV TZ="America/Los_Angeles"

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "playWordle.py"]