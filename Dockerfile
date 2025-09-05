FROM alpine/jmeter:5.6.3

LABEL description="JMeter container for performance testing"
LABEL version="1.0"

ENV JMETER_HOME=/opt/apache-jmeter-5.6.3
ENV JMETER_BIN=${JMETER_HOME}/bin
ENV PATH="${PATH}:${JMETER_BIN}"
# Параметры JVM по умолчанию
ENV HEAP="-Xms6g -Xmx10g"
ENV JVM_ARGS="-XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:G1ReservePercent=20 -XX:MaxMetaspaceSize=1g -XX:+HeapDumpOnOutOfMemoryError -Djavax.net.ssl.trustStore=/jmeter/truststore.jks -Djavax.net.ssl.trustStorePassword=changeit"

WORKDIR /jmeter

# Добавление корневого CA
COPY test.crt /opt/
RUN keytool -importcert -alias test -file /opt/test.crt -keystore /jmeter/truststore.jks -storepass changeit -noprompt

# Создаем все необходимые директории одной командой
RUN mkdir -p results

COPY conf/ conf/
COPY data/ data/
COPY tests/ tests/
COPY utils/ utils/
COPY libs/ ${JMETER_HOME}/lib/

# Добавляем пользователя с ограниченными правами
RUN adduser -D jmeter && \
    chown -R jmeter:jmeter /jmeter

USER jmeter

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD jmeter -v >/dev/null 2>&1 || exit 1

# Используем jmeter как точку входа
ENTRYPOINT ["jmeter"]