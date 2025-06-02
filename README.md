# Benchmark for ReductStore Client SDKs

This repository contains a benchmark for the ReductStore Client SDKs:

- [Rust Client SDK](https://github.com/reductstore/reductstore/tree/main/reduct_rs)
- [Python Client SDK](https://github.com/reductstore/reduct-py)
- [JavaScript Client SDK](https://github.com/reductstore/reduct-js)
- [C++ Client SDK](https://github.com/reductstore/reduct-cpp)
- [Go Client SDK](https://github.com/reductstore/reduct-go)


## Running the benchmark

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- 50 GB of free disk space

### Running the benchmark

1. Clone this repository
2. Run `docker-compose up` in the root directory of this repository
3. Run `python3 build-plot.py` in the root directory of this repository to build plots from the benchmark results