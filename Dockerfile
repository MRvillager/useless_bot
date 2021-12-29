FROM python:3.9-slim-bullseye

ENV BUILD_ONLY_PACKAGES='curl gcc' \
  # python
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # poetry
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  PATH="$PATH:/root/.poetry/bin"

# System deps
RUN apt-get update  \
    && apt-get -y full-upgrade \
    && apt-get install -y $BUILD_ONLY_PACKAGES \
    && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python - \
    && poetry --version \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Change workdir
WORKDIR /bot

# Setting up proper permissions:
RUN groupadd -r bot && useradd -d /bot -r -g bot bot \
    && chown bot:bot -R /bot

# Copy requirements
COPY --chown=bot:bot ./poetry.lock ./pyproject.toml /bot/

# install project dependecies
RUN python -m pip install --upgrade pip \
    && poetry install --no-dev --no-interaction --no-ansi \
    && rm -rf "$POETRY_CACHE_DIR" \

# remove temporary deps
RUN apt-get remove -y $BUILD_ONLY_PACKAGES

# Copy project
COPY --chown=bot:bot . /bot

# run as non-root user
USER bot

# Commands to execute inside container
CMD ["python", "-O", "-B", "-m", "useless_bot"]
