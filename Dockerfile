FROM python:3.8

WORKDIR /bot

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt

COPY . .

CMD ["python3", "./main.py"]
