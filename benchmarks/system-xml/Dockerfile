FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src
COPY SystemXmlBench.csproj Program.cs ./
RUN dotnet publish -c Release -o /app

FROM mcr.microsoft.com/dotnet/runtime:9.0
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /app /app
RUN printf '#!/bin/bash\n/app/SystemXmlBench "$@"\n' > /usr/local/bin/bench && chmod +x /usr/local/bin/bench
COPY runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
