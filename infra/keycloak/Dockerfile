# Bake realm import into the image to avoid Docker Desktop macOS bind-mount
# errors like: mkdir /host_mnt/Users/.../realm-export.json: file exists
FROM quay.io/keycloak/keycloak:26.0

COPY realm-export.json /opt/keycloak/data/import/realm-export.json
