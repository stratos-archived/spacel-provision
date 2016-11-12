#!/bin/sh

PY_PACKAGES="python3"
PY_PACKAGES_BUILD="python3-dev libffi-dev openssl-dev"
PIP_COMMAND="pip3"

if [ "${PYTHON_VERSION}" == "2" ]; then
	PY_PACKAGES="python py-pip"
	PY_PACKAGES_BUILD="python-dev libffi-dev openssl-dev"
	PIP_COMMAND="pip"
fi

apk add --update \
    gcc \
    musl-dev \
    ca-certificates \
    ${PY_PACKAGES} \
    ${PY_PACKAGES_BUILD} \
  && ${PIP_COMMAND} install -r /app/requirements.txt \
  && ${PIP_COMMAND} install -r /app/test-requirements.txt \
  && apk del \
     gcc \
     musl-dev \
     ${PY_PACKAGES_BUILD} \
  && rm -rf /var/cache/apk/*

