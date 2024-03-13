FROM ubuntu:mantic

ENV DEBIAN_FRONTEND="noninteractive" \
    TZ="Etc/UTC" \
    ECCODES_DIR=/opt/eccodes \
    PATH="${PATH}:/opt/eccodes/bin" \
    ECCODES_VER=2.34.1

SHELL ["/bin/bash", "-c"]

# install system packages
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y python3.12 python3.12-dev python3.12-venv python3-pip python3-setuptools \
        vim curl postgresql libpq-dev \
        build-essential cmake gfortran libffi-dev git libudunits2-0

WORKDIR /tmp/eccodes
RUN curl https://confluence.ecmwf.int/download/attachments/45757960/eccodes-${ECCODES_VER}-Source.tar.gz --output eccodes-${ECCODES_VER}-Source.tar.gz
RUN tar xzf eccodes-${ECCODES_VER}-Source.tar.gz
RUN mkdir build && cd build && cmake -DENABLE_AEC=OFF -DCMAKE_INSTALL_PREFIX=${ECCODES_DIR} ../eccodes-${ECCODES_VER}-Source && make && ctest && make install

RUN groupadd -g 1001 wis2
RUN useradd -u 1001 wis2admin
RUN usermod -aG wis2 wis2admin

USER wis2admin
WORKDIR /home/wis2admin

RUN python3.12 -m venv /home/wis2admin/.venv && \
    echo "source /home/wis2admin/.venv/bin/activate" >> .bashrc && \
    echo "" >> .bashrc

RUN source /home/wis2admin/.venv/bin/activate
