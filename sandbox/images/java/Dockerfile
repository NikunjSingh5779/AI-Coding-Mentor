FROM eclipse-temurin:21-jdk-jammy

RUN groupadd --system sandbox && useradd --system --gid sandbox sandbox
ENV HOME=/tmp PATH=/opt/java/openjdk/bin:/usr/local/bin:/usr/bin:/bin
WORKDIR /workspace
RUN mkdir -p /workspace /tmp/work && chown -R sandbox:sandbox /workspace /tmp/work
USER sandbox
CMD ["java", "-version"]
