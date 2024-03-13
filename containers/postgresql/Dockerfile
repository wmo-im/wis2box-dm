FROM postgres:latest

ENV DEBIAN_FRONTEND="noninteractive" \
    TZ="Etc/UTC"

SHELL ["/bin/bash", "-c"]

WORKDIR /local

# install system packages
RUN apt-get update -y && \
    apt-get upgrade && \
    apt-get install -y postgis

