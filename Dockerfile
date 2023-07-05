# Stage 1: Build dependencies
FROM python:3.10-slim AS build

# set work directory
WORKDIR /usr/src/dj_dastore

# install psycopg2 dependencies
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && apt-get -y install libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .
RUN pip install --upgrade pip \
    && pip install pipenv \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir opencv-python-headless

# Stage 2: Build app image
FROM python:3.10-slim

# set work directory
WORKDIR /usr/src/dj_dastore
RUN mkdir /usr/src/dj_dastore/static_cdn
RUN mkdir /usr/src/dj_dastore/media_cdn

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install netcat
RUN apt-get update \
    && apt-get install -y netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/dj_dastore/entrypoint.sh \
    && chmod +x /usr/src/dj_dastore/entrypoint.sh

# copy installed packages from first stage
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=build /usr/lib/x86_64-linux-gnu/libmagic.so.1 /usr/lib/x86_64-linux-gnu/
# copy project
COPY --from=build /usr/src/dj_dastore .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/dj_dastore/entrypoint.sh"]
