FROM ubuntu:22.04

RUN apt update && \
    apt install -y build-essential cmake zip wget git libssl-dev libzip-dev


ARG VERSION=1.11.0
WORKDIR /install
RUN wget https://github.com/reductstore/reduct-cpp/archive/refs/tags/v${VERSION}.zip
RUN unzip v${VERSION}.zip
RUN cd reduct-cpp-${VERSION} && \
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
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make

CMD ["./build/bench-cpp"]
