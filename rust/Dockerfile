FROM rust:1.89.0

COPY src src
COPY Cargo.toml Cargo.toml

RUN cargo build --release
CMD ["cargo", "run", "--release", "--bin", "bench"]