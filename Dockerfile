FROM python:3.6
WORKDIR /opt/aws
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./*.py ./
