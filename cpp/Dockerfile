FROM ubuntu:22.04

RUN apt update && \
    apt install -y build-essential cmake zip wget git libssl-dev libzip-dev


WORKDIR /install
RUN wget https://github.com/reductstore/reduct-cpp/archive/refs/tags/v1.7.0.zip
RUN unzip v1.7.0.zip
RUN cd reduct-cpp-1.7.0 && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install

WORKDIR /app
COPY main.cc .
COPY CMakeLists.txt .
RUN mkdir build && \
    cd build && \
    cmake .. && \
    make

CMD ["./build/bench-cpp"]
