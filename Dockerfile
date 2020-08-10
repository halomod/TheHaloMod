FROM python:3.8-slim-buster

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update
RUN apt-get install -qq -y build-essential gfortran

RUN mkdir /app
WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN bash -c 'echo $(which python)'

COPY requirements.txt ./
RUN python -m pip install wheel
RUN python -m pip install -r requirements.txt
RUN bash -c 'python -m pip freeze'


RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static

RUN mkdir /webhost

RUN adduser --disabled-password --gecos "" user

COPY . ./
RUN ls -la /app

RUN chmod +x entrypoint

USER user

CMD ["sh", "-c", "/app/entrypoint ${PORT}"]
