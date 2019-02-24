FROM python:3.7

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install pip -U
RUN pip install --no-cache-dir -r requirements.txt
COPY Eranox/__init__.py /app/Eranox/__init__.py
COPY Eranox/Server/__init__.py /app/Eranox/Server/__init__.py
COPY Eranox/Core /app/Eranox/Core
COPY Eranox/Core/Message.py /app/Eranox/Server/Message.py
COPY Eranox/Core/Command.py /app/Eranox/Server/Command.py
COPY Eranox/Server/data/certificate.crt /app/Eranox/Server/data/certificate.crt
COPY Eranox/Agent /app/Eranox/Agent
COPY eranox.py /app/eranox.py
COPY Eranox/constants.py /app/Eranox/constants.py


ENTRYPOINT ["python3","/app/eranox.py","-v","agent"]

CMD ["-c /config/config.yml"]