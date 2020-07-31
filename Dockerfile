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
RUN python -m pip install -r requirements.txt
RUN bash -c 'python -m pip freeze'

COPY . ./
RUN ls /app

# RUN mkdir -p /vol/web/media
# RUN mkdir -p /vol/web/static

RUN adduser --disabled-password user
# RUN chown -R user:user /vol
RUN chown -R user:user /opt/venv
RUN chown -R 755 /opt/venv
# RUN chmod -R 755 /vol/web
USER user

RUN python -m
RUN bash -c 'echo $(which gunicorn)'

CMD ["gunicorn", "--chdir", "app", "--bind", ":8000", "TheHaloMod.wsgi:application"]
