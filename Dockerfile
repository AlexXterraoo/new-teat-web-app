CMD ["sh", "-c", "xray -config /etc/xray/config.json & uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
