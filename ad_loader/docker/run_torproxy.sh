#!/bin/sh

podman rm -i torproxy
podman run -d --rm --name torproxy -h torproxy -p 9050 torproxy
