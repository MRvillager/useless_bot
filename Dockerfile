FROM python:3.9-slim-bullseye
WORKDIR /bot

COPY . .

RUN apt-get update && apt-get install --no-install-recommends -y git libffi-dev libnacl-dev python3-dev libopus-dev \
    && /usr/local/bin/python -m pip install --upgrade pip \
    && pip install -i https://www.piwheels.org/simple/ --extra-index-url https://pypi.org/simple/ --no-cache-dir -r requirements.txt \
    && apt-get purge -y git \
    && apt-get autoremove --yes \
    && rm requirements.txt \
    && rm -rf /var/lib/apt/lists/*

# Commands to execute inside container
CMD ["python", "-O", "-B", "-m", "useless_bot"]
