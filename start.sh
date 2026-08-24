#!/bin/sh
uvicorn app:app --host 127.0.0.1 --port 8081 &
xray -config /etc/xray/config.json &
nginx -g 'daemon off;'
