FROM python:3.7

WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY EranoxAuth /app/EranoxAuth
RUN mkdir /config
RUN pip install pip -U
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r EranoxAuth/requirements.txt
COPY Eranox/constants /app/Eranox/constants
COPY Eranox/__init__.py /app/Eranox/__init__.py
COPY Eranox/Server/__init__.py /app/Eranox/Server/__init__.py
COPY Eranox/Core /app/Eranox/Core
COPY Eranox/Server/data/certificate.crt /app/Eranox/Server/data/certificate.crt
COPY Eranox/Agent /app/Eranox/Agent
COPY Eranox/Agent/config.yml /config/config.yml
COPY eranox.py /app/eranox.py


ENTRYPOINT ["python3","/app/eranox.py","-v","agent"]

CMD ["-c", "/config/config.yml"]