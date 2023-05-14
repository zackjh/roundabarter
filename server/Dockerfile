# syntax=docker/dockerfile:1

FROM python:3.11.3-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD ["python3", "-m", "flask", "--app", "api.py", "run", "--host=0.0.0.0"]