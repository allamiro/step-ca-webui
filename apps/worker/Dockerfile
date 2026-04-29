FROM python:3.12-slim

RUN useradd -m -u 10001 appuser

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m venv /home/appuser/venv && chown -R appuser:appuser /home/appuser/venv /app

USER appuser
ENV PATH="/home/appuser/venv/bin:${PATH}"
RUN pip install --no-cache-dir -r /app/requirements.txt
USER root

# Install step-cli for worker-driven certificate operations
ARG TARGETARCH
RUN apt-get update && apt-get install -y curl ca-certificates && rm -rf /var/lib/apt/lists/* \
    && ARCH="${TARGETARCH:-}" \
    && if [ -z "$ARCH" ]; then ARCH="$(dpkg --print-architecture)"; fi \
    && if [ "$ARCH" = "amd64" ]; then STEP_ARCH="amd64"; \
       elif [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then STEP_ARCH="arm64"; \
       else echo "Unsupported architecture: $ARCH (TARGETARCH=${TARGETARCH:-unset})" && exit 1; fi \
    && curl -fsSL "https://dl.smallstep.com/gh-release/cli/docs-cli-install/v0.25.2/step-cli_0.25.2_${STEP_ARCH}.deb" -o /tmp/step-cli.deb \
    && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y /tmp/step-cli.deb \
    && rm -f /tmp/step-cli.deb \
    && chown -R appuser:appuser /app

COPY worker /app/worker
RUN chown -R appuser:appuser /app/worker

USER appuser

CMD ["celery", "-A", "worker.celery_app:celery_app", "worker", "--loglevel=info", "-Q", "pki"]
