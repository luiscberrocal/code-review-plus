ARG PYTHON_VERSION=3.12.11-slim-bookworm

# define an alias for the specfic python version used in this file.
FROM python:${PYTHON_VERSION} as python

# Python build stage
FROM python as python-build-stage

ARG BUILD_ENVIRONMENT=production

ARG PYPI_TOKEN
ENV PYPI_TOKEN $PYPI_TOKEN

# Install apt packages
RUN apt-get update

# dependencies for building Python packages
RUN apt-get install --no-install-recommends -y build-essential \
    # psycopg2 dependencies \
    && apt-get install -y libpq-dev \
    # Install git to get local libs from gitlab
    && apt-get install -y git wget

RUN wget https://github.com/edenhill/librdkafka/archive/v1.9.2.tar.gz  \
    && tar xvzf v1.9.2.tar.gz  \
    && cd librdkafka-1.9.2/  \
    && ./configure  \
    && make  \
    && make install  \
    && ldconfig

# Upgrade security updates
RUN apt upgrade -y

# Requirements are installed here to ensure they will be cached.
COPY ./requirements .

# Create Python Dependency and Sub-Dependency Wheels.
RUN pip wheel --wheel-dir /usr/src/app/wheels  \
  -r ${BUILD_ENVIRONMENT}.txt


# Python 'run' stage
FROM python as python-run-stage

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN addgroup --system django \
    && adduser --system --ingroup django django

# Install required system dependencies
# Install apt packages
RUN apt-get update

# psycopg2 dependencies
RUN apt-get install --no-install-recommends -y libpq-dev \
    # Translations dependencies \
    && apt-get install -y gettext

# Upgrade security updates
RUN apt upgrade -y

# cleaning up unused files
RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# All absolute dir copies ignore workdir instruction. All relative dir copies are wrt to the workdir instruction
# copy python dependency wheels from python-build-stage
COPY --from=python-build-stage /usr/src/app/wheels  /wheels/

# use wheels to install python dependencies
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/

COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY --chown=django:django ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start
RUN chown django /start

COPY ./compose/production/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r//' /start-celeryworker
RUN chmod +x /start-celeryworker
RUN chown django /start-celeryworker

COPY ./compose/production/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r//' /start-celerybeat
RUN chmod +x /start-celerybeat
RUN chown django /start-celerybeat

# copy application code to WORKDIR
COPY --chown=django:django . ${APP_HOME}

# make django owner of the WORKDIR directory as well.
RUN chown django:django ${APP_HOME}

USER django

ENTRYPOINT ["/entrypoint"]
