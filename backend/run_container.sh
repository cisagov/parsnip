#!/bin/bash

# Copyright 2024, Battelle Energy Alliance, LLC All Rights Reserved

# Routine Build
docker build -t parsnip_backend .
# Build that forces everything to be new
#docker build --force-rm --rm --no-cache -t parsnip_backend .
mkdir -p transfer
docker run -t -i -P --rm --entrypoint=/bin/bash  -v $(pwd):/opt/parsnip:rw -w /opt/parsnip parsnip_backend
