FROM python:slim-buster
WORKDIR /usr/src/bot

RUN apt update && apt install -y git \
    && /usr/local/bin/python -m pip install --upgrade pip \
    && pip install -i https://www.piwheels.org/simple/ --extra-index-url https://pypi.org/simple/ --no-cache-dir -r ~/requirements.txt \
    && rm ~/requirements.txt \
    && rm -rf /var/lib/apt/lists/*

# Commands to execute inside container
CMD ["scripts/run_docker.sh"]
