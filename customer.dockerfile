FROM python:3

RUN mkdir -p /opt/src/customer
WORKDIR /opt/src/customer

COPY customer/application.py ./application.py
COPY products/configuration.py ./products/configuration.py
COPY products/models.py ./products/models.py
COPY decorator.py ./decorator.py
COPY products/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/customer"

ENTRYPOINT ["python", "./application.py"]