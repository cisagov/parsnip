#!/bin/bash

# Copyright 2024, Battelle Energy Alliance, LLC All Rights Reserved

hostPort=5000
dockerPort=5000
docker build -t flask-app .
docker run -t -i -P --rm --entrypoint=/bin/bash -p $hostPort:$dockerPort -v $(pwd)/app:/opt/app:rw flask-app
