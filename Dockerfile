FROM ghcr.io/nginx/nginx-unprivileged:1.30.4-alpine3.24@sha256:44e36330f74d4f3a1d4e222acca9e23b401fb87811a7597024502bb759c4dd49

ARG ATLAS_VERSION=1.2.0
LABEL org.opencontainers.image.title="Scientific Data Lifecycle Atlas" \
      org.opencontainers.image.description="Standalone static lifecycle and evidence-mapping reference" \
      org.opencontainers.image.version="${ATLAS_VERSION}"

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docs/lifecycle-atlas/ /usr/share/nginx/html/

USER 101
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/healthz"]
