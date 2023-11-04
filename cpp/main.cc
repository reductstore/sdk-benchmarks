#include <reduct/client.h>
#include <iostream>
#include <cmath>
#include <fstream>


using reduct::IClient;
using reduct::HttpOptions;

struct Result {
    double write_rec_per_sec;
    double write_bytes_per_sec;
    double read_rec_per_sec;
    double read_bytes_per_sec;
    size_t record_size;
    size_t record_count;
};


auto bench = [](auto record_size, auto record_count) -> Result {
    auto result = Result{};
    result.record_size = record_size;
    result.record_count = record_count;

    auto client = reduct::IClient::Build(
            "http://reductstore:8383",
            HttpOptions{
                    .api_token = "token",
            }
    );

    auto [bucket, err] = client->GetBucket("benchmark");
    if (err) {
        throw std::runtime_error("Failed to get bucket: " + err.ToString());
    }
    std::string data(record_size, 'x');

    auto start = IClient::Time::clock::now();
    auto measure_time = start;
    for (auto i = 0; i < record_count; ++i) {
        auto write_err = bucket->Write("cpp-bench", std::nullopt, [&data](auto record) {
            record->WriteAll(data);
        });
        if (write_err) {
            throw std::runtime_error("Failed to write record: " + write_err.ToString());
        };
    }

    auto end = IClient::Time::clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    result.write_rec_per_sec = record_count / (elapsed / 1000000.0);
    result.write_bytes_per_sec = result.write_rec_per_sec * record_size;

    size_t count = 0;
    start = IClient::Time::clock::now();
    err = bucket->Query("cpp-bench", measure_time, std::nullopt, {}, [&count](auto record) {
        auto [content, read_err] = record.ReadAll();
        if (read_err) {
            throw std::runtime_error("Failed to read record: " + read_err.ToString());
        }
        count += content.size();
        return true;
    });

    if (err) {
        throw std::runtime_error("Failed to query records:" + err.ToString());
    }

    if (count != record_count * record_size) {
        throw std::runtime_error(
                "Size mismatch: " + std::to_string(count) + " != " + std::to_string(record_count * record_size));
    }

    end = IClient::Time::clock::now();
    elapsed = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    result.read_rec_per_sec = record_count / (elapsed / 1000000.0);
    result.read_bytes_per_sec = result.read_rec_per_sec * record_size;

    return result;
};

template<typename Os>
void print_result(Os &os, const Result &result) {
    os << result.record_size << "," << result.record_count << "," << result.write_rec_per_sec << ","
        << result.write_bytes_per_sec << "," << result.read_rec_per_sec << "," << result.read_bytes_per_sec
        << std::endl;
}

int main() {

    std::ofstream csv("/results/cpp.csv");
    for (auto i = 0; i < 15; ++i) {
        auto result = bench(std::pow(2, i) * 1024, 1000);
        print_result(csv, result);
        print_result(std::cout, result);
    }
    return 0;
}