FROM --platform=${TARGETPLATFORM} python:3.10.8-slim-buster as builder

RUN mkdir /build && python -m pip install pip --upgrade && python -m pip install build

WORKDIR /build
ADD . .

RUN python -m build


FROM --platform=${TARGETPLATFORM} alpine:latest as compiler

USER root

RUN apk add --update libffi-dev gcc musl-dev python3 python3-dev && mkdir /install && mkdir -p /opt/venv && python3 -m venv /opt/venv

COPY --from=builder /build/dist/step_npm_plugin-0.1-py3-none-any.whl /install
ENV PATH="/opt/venv/bin:$PATH"

RUN python -m pip install /install/step_npm_plugin-0.1-py3-none-any.whl


FROM --platform=${TARGETPLATFORM} smallstep/step-cli:0.22.1-rc16

USER root

RUN adduser -s /bin/sh -D npm_step && apk add --update python3

COPY --from=compiler /opt/venv /opt/venv

WORKDIR /home/npm_step
USER npm_step
ENV PATH="/opt/venv/bin:$PATH"
ENV STEP="/home/npm_step"
ENV STEPPATH="/home/npm_step"

ENTRYPOINT ["python", "-m", "step_npm_plugin"]
