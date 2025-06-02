FROM golang:1.24

WORKDIR /app
COPY . .
RUN go get all

CMD ["go", "run", "benchmark.go"]