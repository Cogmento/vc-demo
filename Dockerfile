FROM python:3.11-alpine

ENV PYTHONPATH=/opt/vc-demo

WORKDIR /opt/vc-demo

ADD . /opt/vc-demo

# Run pip to install all requirements
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["gunicorn", "--conf", "conf.py", "--bind", "0.0.0.0:8000", "main:app"]
