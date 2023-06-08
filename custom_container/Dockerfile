FROM --platform=linux/amd64 ubuntu:22.04

RUN apt-get -y update
RUN apt-get install -y --no-install-recommends \
python3-pip \
pipx \
git \
make \
jq

RUN pip install \
argcomplete>=1.9.4 \
poetry==1.1.14 \
jupyterlab==3.3.0

RUN pwd

# Create a link that points to the right python bin directory
RUN ln -s /usr/bin/python3 /usr/bin/python3.7

# ENABLE:
# Notebooks API
# Container Registry API
# Artifact Registry API