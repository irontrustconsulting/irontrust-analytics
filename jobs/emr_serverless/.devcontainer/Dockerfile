# Amazon Linux 2023 base image (matches EMR 7.x family OS)
FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# ========== System dependencies ==========
# - Python 3.11 toolchain
# - Amazon Corretto 17 (Spark-compatible JDK for AL2023)
# - Common build tools for native wheels
# - NOTE: Do NOT install 'curl' (base has curl-minimal) to avoid conflicts.
RUN dnf update -y && \
    dnf install -y \
        python3.11 python3.11-devel python3.11-pip \
        java-17-amazon-corretto java-17-amazon-corretto-devel \
        git tar gzip zip unzip which findutils \
        gcc gcc-c++ make openssl-devel libffi-devel && \
    # Provide a 'python' shim for tools that expect it (alternatives isn't set up by default)
    ln -s /usr/bin/python3.11 /usr/bin/python && \
    dnf clean all

# Make JDK explicit on PATH
ENV JAVA_HOME=/usr/lib/jvm/java-17-amazon-corretto
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# ========== Python tooling ==========
# Upgrade pip and install Poetry (into /root/.local/bin)
RUN python3.11 -m pip install --upgrade pip
RUN curl -sSL https://install.python-poetry.org | python3.11 -
ENV PATH="/root/.local/bin:${PATH}"

# ========== PySpark for your experiment ==========
# If you want to test with Spark 4.x in your venv, we install a matching PySpark here too,
# mainly for local dev convenience. You can change this ARG to 3.5.6 later to align exactly
# with EMR 7.12.0, or remove it and rely purely on the runtime venv you package.
ARG Pyspark_Version=4.1.1
RUN pip install "pyspark==${Pyspark_Version}"

# venv-pack is required to package the EMR runtime environment
RUN pip install venv-pack

# ========== AWS CLI v2 ==========
# The base image has curl-minimal, which provides /usr/bin/curl—sufficient for AWS CLI download.
RUN curl -sS https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o awscliv2.zip && \
    unzip -q awscliv2.zip && ./aws/install && rm -rf awscliv2.zip aws/

# Working directory where your EMR folder is bind-mounted
WORKDIR /workspace