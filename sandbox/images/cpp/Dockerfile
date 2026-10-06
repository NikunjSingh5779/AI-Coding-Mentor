FROM gcc:14-bookworm

RUN groupadd --system sandbox && useradd --system --gid sandbox sandbox
ENV HOME=/tmp PATH=/usr/local/bin:/usr/bin:/bin
WORKDIR /workspace
RUN mkdir -p /workspace /tmp/work && chown -R sandbox:sandbox /workspace /tmp/work
USER sandbox
CMD ["g++", "--version"]
