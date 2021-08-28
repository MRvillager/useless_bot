FROM python:slim-buster
WORKDIR /bot

COPY . .

RUN apt update && apt install -y git \
    && /usr/local/bin/python -m pip install --upgrade pip \
    && pip install -i https://www.piwheels.org/simple/ --extra-index-url https://pypi.org/simple/ --no-cache-dir -r requirements.txt \
    && apt purge -y git \
    && rm requirements.txt \
    && rm -rf /var/lib/apt/lists/*

# Commands to execute inside container
CMD ["python", "-O", "-B", "-m", "useless_bot"]
