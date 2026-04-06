FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc && rm -rf /var/lib/apt/lists/*
COPY bench.py /usr/local/bin/bench.py
RUN printf '#!/bin/bash\npython3 /usr/local/bin/bench.py "$@"\n' > /usr/local/bin/bench && chmod +x /usr/local/bin/bench
COPY runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
