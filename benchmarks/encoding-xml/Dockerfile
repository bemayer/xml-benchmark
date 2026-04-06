FROM golang:bookworm AS build
WORKDIR /src
COPY go.mod main.go ./
RUN CGO_ENABLED=0 go build -o bench .

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/bench /usr/local/bin/bench
COPY runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
