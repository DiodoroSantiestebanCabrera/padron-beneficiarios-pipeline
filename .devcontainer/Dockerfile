FROM mcr.microsoft.com/devcontainers/base:bookworm@sha256:86165cfc170e9b2aa8df90b847127eea97b08eb9987021e6e6ec6c3a96545d7c

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11.20 /uv /uvx /bin/
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh \
    | bash -s -- --tag 1.46.0 --to /usr/local/bin