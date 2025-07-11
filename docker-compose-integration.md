# Docker Compose Integration Plan

## (a) Codebase Review

### Dockerfiles and Images
- The repository contains one Dockerfile at the project root used to build the KiCad v5 + SKiDL environment.
- Calculations currently run inside ephemeral `python:3.12-slim` containers started via `docker run`.
- MCP server is launched through the `ghcr.io/shaurya-sethi/circuitron-mcp:latest` image using `docker run`.

### Environment Loading
- Environment variables are loaded by `circuitron.config` from a `.env` file located at `~/.circuitron/.env` (or the path set in `CIRCUITRON_ENV_FILE`).
- `setup_environment` validates that several variables are present, including OpenAI, Supabase and Neo4j credentials and `MCP_URL`.
- `onboarding.run_onboarding` populates that same `.env` file and presets values for the MCP server configuration such as `HOST`, `PORT`, `MODEL_CHOICE` etc.
- The MCP Docker container is started by `mcp_server.start`, which injects these variables when calling `docker run`.
- When creating an MCP client connection, the code checks `DOCKER_ENV` to adjust timeouts.

## (b) Step-by-Step Docker Compose Integration Plan

1. **Add `docker-compose.yml` to the repository**
   - Define three services: `math-sandbox`, `kicad-skidl`, and `mcp-server`.
   - Use the published images `python:3.12-slim`, `ghcr.io/shaurya-sethi/circuitron-kicad:latest`, and `ghcr.io/shaurya-sethi/circuitron-mcp:latest` respectively.
   - Set `container_name` for deterministic management (e.g. `circuitron-math-sandbox`).

2. **Environment variables**
   - Hardcode fixed MCP settings (`HOST`, `PORT`, `TRANSPORT`, `MODEL_CHOICE`, `USE_*`, `LLM_MAX_CONCURRENCY`, `LLM_REQUEST_DELAY`).
   - Load user-provided secrets (`OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`) from an external `.env` file referenced via `env_file:`.
   - Keep this `.env` file out of version control (add to `.gitignore`). Provide a template `compose.env.example` for users.

3. **Container isolation**
   - `math-sandbox` and `kicad-skidl` containers run with `network_mode: none` and resource limits (`mem_limit`, `pids_limit`) matching the current `docker run` commands.
   - `mcp-server` exposes port `8051` to the host.
   - No inter-container networking is defined since the services operate independently.

4. **Programmatic Compose Invocation**
   - Replace direct `docker` calls in `DockerSession` and `mcp_server` with helper functions that run `docker compose` commands (e.g. `subprocess.run(["docker", "compose", "up", "-d", "kicad-skidl"])`).
   - Circuitron’s CLI should check container status using `docker compose ps` and invoke `docker compose pull` on first run.
   - Calculations that currently use `docker run` should instead execute inside `math-sandbox` via `docker compose exec math-sandbox python -c <code>`.
   - Provide cleanup via `docker compose stop`/`docker compose down` when sessions end.

5. **`.env` Management**
   - Users run `circuitron config` (existing onboarding) which writes credentials to `~/.circuitron/.env`.
   - The same file path should be referenced in `docker-compose.yml` using `env_file:` so both Circuitron and the MCP container share credentials.
   - Document that this `.env` must exist before running Circuitron. Include an ignored sample `.env` (`compose.env.example`) showing required keys.

6. **Documentation & Onboarding**
   - Update README with a brief section on Docker Compose usage: install Docker & Docker Compose, run `circuitron` which automatically starts the stack, and stop containers with `circuitron --down` (to be implemented).

## (c) Example `docker-compose.yml`
```yaml
version: "3.9"
services:
  math-sandbox:
    image: python:3.12-slim
    container_name: circuitron-math-sandbox
    command: sleep infinity
    network_mode: none
    mem_limit: 128m
    pids_limit: 64

  kicad-skidl:
    image: ghcr.io/shaurya-sethi/circuitron-kicad:latest
    container_name: circuitron-kicad
    command: sleep infinity
    network_mode: none
    mem_limit: 512m
    pids_limit: 256

  mcp-server:
    image: ghcr.io/shaurya-sethi/circuitron-mcp:latest
    container_name: circuitron-mcp
    ports:
      - "8051:8051"
    env_file:
      - ~/.circuitron/.env
    environment:
      HOST: "0.0.0.0"
      PORT: "8051"
      TRANSPORT: "sse"
      MODEL_CHOICE: "gpt-4.1-nano"
      USE_CONTEXTUAL_EMBEDDINGS: "true"
      USE_HYBRID_SEARCH: "true"
      USE_AGENTIC_RAG: "true"
      USE_RERANKING: "true"
      USE_KNOWLEDGE_GRAPH: "true"
      LLM_MAX_CONCURRENCY: "2"
      LLM_REQUEST_DELAY: "0.5"
```

## (d) Recommended Improvements / Best Practices
- Consider adding a lightweight health check in the Compose file for the MCP server (`healthcheck:`) to detect start-up failures quickly.
- Use a dedicated Docker network for Circuitron services if future components need to communicate, though currently isolation via `network_mode: none` is sufficient.
- Provide a `circuitron compose` command exposing operations like `up`, `down`, `pull`, and `logs` for power users who want direct control.
- Keep credentials outside the repo and document environment variables clearly in `compose.env.example`.
- Regularly update the container images using `docker compose pull` during installation or as part of an automated update command within Circuitron.
