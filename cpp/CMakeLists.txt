cmake_minimum_required(VERSION 3.18)

project(bench-cpp)
set(CMAKE_CXX_STANDARD 20)

find_package(ZLIB)
find_package(OpenSSL)



find_package(ReductCpp 1.7.0)

add_executable(bench-cpp main.cc)
target_link_libraries(bench-cpp ${REDUCT_CPP_LIBRARIES} ${ZLIB_LIBRARIES} OpenSSL::SSL OpenSSL::Crypto)
