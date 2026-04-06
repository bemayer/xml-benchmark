FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake git ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY CMakeLists.txt bench.cpp ./
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j$(nproc)

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/build/bench /usr/local/bin/bench
COPY runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
