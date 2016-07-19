FROM alpine:3.4

COPY requirements.txt /app/requirements.txt

RUN apk add --update \
    python3 \
  && pip3 install -r /app/requirements.txt \
  && rm -rf /var/cache/apk/*

COPY src/ /app
WORKDIR /app

ENTRYPOINT ["/usr/bin/python", "-m", "spacel.main"]

