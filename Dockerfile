# Use the official Python 3.12 slim image as a base
FROM python:3.12-slim

# Set environment variables to non-interactive to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages: wget for downloading and unzip for extracting archives
RUN apt-get update && apt-get install -y --no-install-recommends wget unzip && rm -rf /var/lib/apt/lists/*

# --- Install KiCad v5 Symbols ---
# Set the URL for the KiCad v5 symbols
ARG KICAD_SYMBOLS_URL="https://gitlab.com/kicad/libraries/kicad-symbols/-/archive/5.1.10/kicad-symbols-5.1.10.zip"
# Create the target directory for symbols
RUN mkdir -p /usr/share/kicad/library
# Download and extract the symbols
RUN wget -q -O symbols.zip "${KICAD_SYMBOLS_URL}" && \
    unzip -q symbols.zip -d /usr/share/kicad/library && \
    mv /usr/share/kicad/library/kicad-symbols-5.1.10/* /usr/share/kicad/library/ && \
    rm -rf /usr/share/kicad/library/kicad-symbols-5.1.10 && \
    rm symbols.zip

# --- Install KiCad v5 Footprints ---
# Set the URL for the KiCad v5 footprints
ARG KICAD_FOOTPRINTS_URL="https://gitlab.com/kicad/libraries/kicad-footprints/-/archive/5.1.10/kicad-footprints-5.1.10.zip"
# Create the target directory for footprints
RUN mkdir -p /usr/share/kicad/modules
# Download and extract the footprints
RUN wget -q -O footprints.zip "${KICAD_FOOTPRINTS_URL}" && \
    unzip -q footprints.zip -d /usr/share/kicad/modules && \
    mv /usr/share/kicad/modules/kicad-footprints-5.1.10/* /usr/share/kicad/modules/ && \
    rm -rf /usr/share/kicad/modules/kicad-footprints-5.1.10 && \
    rm footprints.zip

# --- Configure Environment for SKiDL ---
# Set environment variables to point SKiDL to the new library locations
ENV KICAD_SYMBOL_DIR="/usr/share/kicad/library"
ENV KICAD_FOOTPRINT_DIR="/usr/share/kicad/modules"

# --- Install SKiDL ---
# Install the skidl library using pip
RUN pip install --no-cache-dir skidl

# Set the default command to run when the container starts
CMD ["python"]
