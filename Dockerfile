FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        software-properties-common \
        wget && rm -rf /var/lib/apt/lists/*

# -- KiCad 5.1 --
RUN add-apt-repository --yes ppa:kicad/kicad-5.1-releases && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        kicad \
        kicad-symbols \
        kicad-footprints \
        kicad-packages3d && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# -- Python 3.12 --
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.12 \
        python3.12-distutils \
        python3-pip && \
    rm -rf /var/lib/apt/lists/*
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip3 install --no-cache-dir poetry
ENV POETRY_VIRTUALENVS_CREATE=false
WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-dev --no-interaction --no-ansi

COPY . .

EXPOSE 8000
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
# VOLUME ["./backend:/app/backend"]
