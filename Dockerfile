FROM python:3.8.5-slim-buster

ENV PYTHONUNBUFFERED=1

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY main.py /main.py

ENTRYPOINT ["python", "/main.py"]