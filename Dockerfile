# hadolint global ignore=DL3008
FROM debian:buster

# Set Docker User and Group IDs for matching with host
ARG UID=510
ARG GID=510

# Install OSQA dependencies and cleanup apt cache
RUN apt-get update && apt-get install -y --no-install-recommends \
      python \
      python-pip \
      python-dev \
      python-setuptools \
      ca-certificates \
      gcc \
      libpq-dev \
      curl \
      gunicorn \
      gettext \
    && rm -rf /var/lib/apt/lists/*

# Ensure terminate if pipefail
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Create OSQA user and group
RUN groupadd --system --gid ${GID} osqa && useradd --system --gid osqa --uid ${UID} osqa

# Create OSQA working directory
WORKDIR /srv/app
# Set OSQA user as owner of working directory to allow .pyc files can be created
RUN chown osqa:osqa /srv/app

# Install OSQA requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy OSQA source code into container
COPY --chown=osqa . .

# Set Container Default Environment Variables. Override as appropriate at runtime.
ENV OSQA_DB_ENGINE=django.db.backends.postgresql_psycopg2
ENV OSQA_DB_NAME=osqa
ENV OSQA_DB_USER=osqa
ENV OSQA_DB_PASSWORD=osqa
ENV OSQA_DB_HOST=postgres
ENV OSQA_ALLOWED_HOSTS=localhost
ENV OSQA_CACHE_BACKEND=memcached://memcached:11211/
ENV OSQA_APP_URL=http://localhost:8080/
ENV OSQA_TIME_ZONE=UTC

# Set container entrypoint script for runtime container setup
ENTRYPOINT ["./docker/entrypoint.sh"]

# Switch to underprivileged OSQA user
USER osqa

# Expose port 8080 for OSQA
EXPOSE 8080

# Run OSQA
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
