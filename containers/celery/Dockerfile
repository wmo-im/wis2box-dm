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
    apt-get install -y python3.12 python3.12-venv python3-pip python3-setuptools python3.12-dev vim curl libpq-dev \
        build-essential cmake gfortran libffi-dev git libudunits2-0


WORKDIR /tmp/eccodes
RUN curl https://confluence.ecmwf.int/download/attachments/45757960/eccodes-${ECCODES_VER}-Source.tar.gz --output eccodes-${ECCODES_VER}-Source.tar.gz
RUN tar xzf eccodes-${ECCODES_VER}-Source.tar.gz
RUN mkdir build && cd build && cmake -DENABLE_AEC=OFF -DCMAKE_INSTALL_PREFIX=${ECCODES_DIR} ../eccodes-${ECCODES_VER}-Source && make && ctest && make install


RUN groupadd -g 1001 wis2
RUN useradd -u 1001 wis2dm
RUN usermod -aG wis2 wis2dm

USER wis2dm
WORKDIR /home/wis2dm

RUN python3.12 -m venv /home/wis2dm/.venv && \
    echo "source /home/wis2dm/.venv/bin/activate" >> .bashrc && \
    echo "" >> .bashrc

COPY ./modules/ ./app

USER root
# Update owner and install
RUN chown -R wis2dm:wis2 ./app

USER wis2dm
RUN cd ./app && \
    source /home/wis2dm/.venv/bin/activate && \
    pip install -e station_metadata && \
    pip install -e wccdm && \
    pip install -e task_manager && \
    pip install -e subscription_manager && \
    pip install https://github.com/david-i-berry/bufr2geojson/archive/wccdm.zip

# now the default command
CMD ["/bin/bash", "-c", "source .venv/bin/activate && task_manager_start worker --concurrency=16 --max-tasks-per-child 100"]