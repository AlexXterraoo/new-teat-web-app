FROM alpine:3.19

RUN apk add --no-cache \
    curl \
    bash \
    ca-certificates \
    tzdata \
    python3 \
    py3-pip \
    jq \
    unzip \
    && ln -sf /usr/share/zoneinfo/Asia/Tehran /etc/localtime

ARG XRAY_VERSION=v1.8.24
RUN curl -L -o /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-64.zip \
    && mkdir -p /usr/local/xray \
    && unzip /tmp/xray.zip -d /usr/local/xray \
    && rm /tmp/xray.zip \
    && chmod +x /usr/local/xray/xray

ENV PATH="/usr/local/xray:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY app.py .
COPY config.json /etc/xray/config.json
COPY templates/ /app/templates/
COPY static/ /app/static/

EXPOSE 8080
CMD ["sh", "-c", "uvicorn app:app --host 127.0.0.1 --port 8081 & xray -config /etc/xray/config.json"]
