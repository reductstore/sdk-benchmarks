cmake_minimum_required(VERSION 3.23)

project(bench-cpp)
set(CMAKE_CXX_STANDARD 20)

find_package(ZLIB)
find_package(OpenSSL)



find_package(reductcpp 1.16.0 REQUIRED)

add_executable(bench-cpp main.cc)
target_link_libraries(bench-cpp reductcpp::reductcpp ${ZLIB_LIBRARIES} OpenSSL::SSL OpenSSL::Crypto)
