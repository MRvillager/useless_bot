FROM python:slim-buster
WORKDIR /bot

COPY . .

RUN /usr/local/bin/python -m pip install --upgrade pip \
    && pip install -i https://www.piwheels.org/simple/ --extra-index-url https://pypi.org/simple/ --no-cache-dir -r requirements.txt \
    && pip uninstall pip \
    && rm requirements.txt

# Commands to execute inside container
CMD ["python -O -B -m useless_bot"]
