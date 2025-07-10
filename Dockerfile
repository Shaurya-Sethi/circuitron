# Use Ubuntu 20.04 - this is required for KiCad 5.1 compatibility
FROM ubuntu:20.04

# Set environment variables to non-interactive to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages: sudo, keyboard-configuration, software-properties-common, wget, unzip, Python 3, and Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    keyboard-configuration \
    software-properties-common \
    wget \
    unzip \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Install Node.js (required for netlistsvg) ---
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# --- Install KiCad 5.1 using the official PPA ---
# Add the KiCad PPA for version 5.1 and install KiCad
RUN add-apt-repository --yes ppa:kicad/kicad-5.1-releases && \
    apt-get update && \
    apt-get install -y --no-install-recommends kicad && \
    rm -rf /var/lib/apt/lists/*

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
ENV KISYSMOD="/usr/share/kicad/modules"

# --- Create SKiDL configuration file ---
RUN mkdir -p /root && \
    echo '{\n\
    "cfg_file_name": ".skidlcfg",\n\
    "tool": "kicad5",\n\
    "pickle_dir": "./lib_pickle_dir",\n\
    "lib_search_paths": {\n\
        "kicad5": [\n\
            ".",\n\
            "/usr/share/kicad/library"\n\
        ]\n\
    },\n\
    "backup_lib_name": "__init___lib",\n\
    "backup_lib_file_name": "__init___lib_sklib.py",\n\
    "query_backup_lib": true,\n\
    "backup_lib": null,\n\
    "footprint_search_paths": {\n\
        "kicad5": "/usr/share/kicad/modules"\n\
    }\n\
}' > /root/.skidlcfg

# --- Create KiCad configuration directory and copy fp-lib-table to expected locations ---
RUN mkdir -p /root/.config/kicad && \
    cp /usr/share/kicad/modules/fp-lib-table /root/.config/kicad/fp-lib-table

# --- Install SKiDL and Python Development Tools ---
# Upgrade pip and install the skidl library and other useful Python packages
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir skidl numpy matplotlib

# --- Install netlistsvg for SKiDL SVG export ---
RUN npm install -g netlistsvg@1.0.2

# Set working directory
WORKDIR /workspace

# Set the default command to run when the container starts
CMD ["python3"]
