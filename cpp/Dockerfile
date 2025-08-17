FROM ubuntu:24.04

RUN apt update && \
    apt install -y build-essential cmake zip wget git libssl-dev pkg-config \
        libfmt-dev \
        nlohmann-json3-dev \
        libcpp-httplib-dev \
        libconcurrentqueue-dev \
        libhowardhinnant-date-dev


ARG VERSION=1.16.0
WORKDIR /install
RUN wget https://github.com/reductstore/reduct-cpp/archive/refs/tags/v${VERSION}.zip
RUN unzip v${VERSION}.zip
RUN cd reduct-cpp-${VERSION} && \
    mkdir build && \
    cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release   && \
    cmake --build . --target install

WORKDIR /app
COPY main.cc .
COPY CMakeLists.txt .
RUN mkdir build && \
    cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release  && \
    cmake --build .

CMD ["./build/bench-cpp"]
