FROM node:22-bookworm-slim

RUN groupadd --system sandbox && useradd --system --gid sandbox sandbox
ENV HOME=/tmp PATH=/usr/local/bin:/usr/bin:/bin NODE_OPTIONS=--disable-proto=delete
WORKDIR /workspace
RUN mkdir -p /workspace /tmp/work && chown -R sandbox:sandbox /workspace /tmp/work
USER sandbox
CMD ["node", "--version"]
