FROM python:3.8-slim-buster

ENV PATH="/scripts:${PATH}" \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update
RUN apt-get install -qq -y build-essential gfortran

RUN mkdir /app
WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . ./
RUN ls /app

RUN chmod +x /app/scripts/*

RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static

RUN adduser --disabled-password user
RUN chown -R user:user /vol
RUN chmod -R 755 /vol/web
USER user

CMD ["gunicorn", "--chdir", "app", "--bind", ":8000", "TheHaloMod.wsgi:application"]
