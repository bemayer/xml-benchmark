FROM node:20-slim AS build
WORKDIR /src
COPY package.json ./
RUN npm install --production

FROM node:20-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/node_modules /app/node_modules
COPY bench.js /app/bench.js
COPY package.json /app/package.json
RUN printf '#!/bin/bash\nnode /app/bench.js "$@"\n' > /usr/local/bin/bench && chmod +x /usr/local/bin/bench
COPY runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
