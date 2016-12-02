#!/bin/bash

# Where to find AWS credentials:
AWS_CREDS_FILE="${HOME}/.aws/credentials"
if [ -f "$AWS_CREDS_FILE" ]; then
	AWS_CREDS="-v ${AWS_CREDS_FILE}:/root/.aws/credentials"
else
	echo "Unable to find AWS credentials"
	exit 1
fi

# Pass through environment variables:
if [ -n "${SPACEL_ORBIT}" ]; then
	SPACEL_ENV="${SPACEL_ENV} -e SPACEL_ORBIT=${SPACEL_ORBIT}"
fi
if [ -n "${SPACEL_APP}" ]; then
	SPACEL_ENV="${SPACEL_ENV} -e SPACEL_APP=${SPACEL_APP}"
fi
if [ -n "${SPACEL_LOG_LEVEL}" ]; then
	SPACEL_ENV="${SPACEL_ENV} -e SPACEL_LOG_LEVEL=${SPACEL_LOG_LEVEL}"
fi
if [ -n "${LAMBDA_BUCKET}" ]; then
	SPACEL_ENV="${SPACEL_ENV} -e LAMBDA_BUCKET=${LAMBDA_BUCKET}"
fi
if [ -n "${LAMBDA_REGION}" ]; then
	SPACEL_ENV="${SPACEL_ENV} -e LAMBDA_REGION=${LAMBDA_REGION}"
fi
if [ -n "${SPACEL_AGENT_CHANNEL}" ]; then
	SPACEL_ENV="${SPACEL_ENV} -e SPACEL_AGENT_CHANNEL=${SPACEL_AGENT_CHANNEL}"
fi


# Which container to use:
SPACEL_CONTAINER="pebbletech/spacel-provision:latest"

docker run -i --rm ${AWS_CREDS} -v `pwd`:/pwd ${SPACEL_ENV} ${SPACEL_CONTAINER} "$@"

