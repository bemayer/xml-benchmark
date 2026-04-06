FROM maven:3-eclipse-temurin-21 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn dependency:resolve
COPY src/ src/
RUN mvn package -q -DskipTests

FROM eclipse-temurin:21-jre
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/target/xerces-bench-1.0.jar /app/bench.jar
RUN printf '#!/bin/bash\njava -jar /app/bench.jar "$@"\n' > /usr/local/bin/bench && chmod +x /usr/local/bin/bench
COPY runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
