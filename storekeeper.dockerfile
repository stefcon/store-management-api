FROM python:3

RUN mkdir -p /opt/src/storekeeper
WORKDIR /opt/src/storekeeper

COPY storekeeper/application.py ./application.py
COPY products/configuration.py ./configuration.py
COPY products/requirements.txt ./requirements.txt
COPY decorator.py ./decorator.py

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/storekeeper"

ENTRYPOINT ["python", "./application.py"]