FROM python:3

RUN mkdir -p /opt/src/products
WORKDIR /opt/src/products

COPY products/manage.py ./manage.py
COPY products/configuration.py ./configuration.py
COPY products/models.py ./models.py
COPY products/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./manage.py"]