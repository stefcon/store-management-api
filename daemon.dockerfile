FROM python:3

RUN mkdir -p /opt/src/daemon
WORKDIR /opt/src/daemon

COPY daemon/application.py ./application.py
COPY products/configuration.py ./products/configuration.py
COPY products/models.py ./products/models.py
COPY products/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/daemon"

ENTRYPOINT ["python", "./application.py"]