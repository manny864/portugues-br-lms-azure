# Imagen personalizada opcional para el Self-Hosted Runner de GitHub Actions en Azure
# Incluye GitHub Actions Runner + Azure CLI + Terraform + Node.js 20 + Python 3 + FFmpeg (para conversión a .opus)
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ARG RUNNER_VERSION="2.319.1"
ARG TERRAFORM_VERSION="1.9.5"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    jq \
    unzip \
    gnupg \
    lsb-release \
    python3 \
    python3-pip \
    ffmpeg \
    libicu70 \
    && rm -rf /var/lib/apt/lists/*

# Instalar Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Instalar Terraform
RUN curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" -o terraform.zip \
    && unzip terraform.zip -d /usr/local/bin \
    && rm terraform.zip

# Crear usuario no-root para el runner
RUN useradd -m -s /bin/bash runner && mkdir -p /actions-runner && chown -R runner:runner /actions-runner

WORKDIR /actions-runner
USER runner

RUN curl -o actions-runner.tar.gz -L "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" \
    && tar xzf ./actions-runner.tar.gz \
    && rm actions-runner.tar.gz

COPY --chown=runner:runner entrypoint.sh /actions-runner/entrypoint.sh
RUN chmod +x /actions-runner/entrypoint.sh

ENTRYPOINT ["/actions-runner/entrypoint.sh"]
