import asyncio
from dataclasses import dataclass
import time
from datetime import datetime

from reduct import Client, Bucket

RECORD_NUM = 1000
RECORD_SIZES = [2**x * 1024 for x in range(15)]  # 1 KiB ~ 16 MiB


class Result:
    write_req_per_sec: float
    write_bytes_per_sec: float
    read_req_per_sec: float
    read_bytes_per_sec: float
    record_size: int
    record_num: int

    def __int__(self):
        self.write_req_per_sec = 0
        self.write_bytes_per_sec = 0
        self.read_req_per_sec = 0
        self.read_bytes_per_sec = 0
        self.record_size = 0
        self.record_num = 0

    def __str__(self):
        return (
            f"Record size: {self.record_size // 1024} KiB, Record num: {self.record_num}, "
            f"Write req/s: {self.write_req_per_sec}, Write KiB/s: {self.write_bytes_per_sec // 1024}, "
            f"Read req/s: {self.read_req_per_sec}, Read KiB/s: {self.read_bytes_per_sec // 1024}"
        )

    def to_csv(self):
        return (
            f"{self.record_size},{self.record_num},{self.write_req_per_sec},"
            f"{self.write_bytes_per_sec},{self.read_req_per_sec},{self.read_bytes_per_sec}"
        )


async def bench(record_size: int, record_num: int) -> Result:
    result = Result()
    result.record_size = record_size
    result.record_num = record_num

    measure_time = time.time_ns() // 1000
    async with Client("http://reductstore:8383", api_token="token") as client:
        bucket: Bucket = await client.get_bucket("benchmark")
        record_data = b"0" * record_size
        start_time = datetime.now()
        for i in range(record_num):
            await bucket.write("python-bench", record_data, time.time_ns() // 1000)
        delta = (datetime.now() - start_time).total_seconds()
        result.write_req_per_sec = int(record_num / delta)
        result.write_bytes_per_sec = int(record_num * record_size / delta)

        start_time = datetime.now()
        async for record in bucket.query(
            "python-bench", start=measure_time, limit=record_num
        ):
            _ = await record.read_all()

        delta = (datetime.now() - start_time).total_seconds()
        result.read_req_per_sec = int(record_num / delta)
        result.read_bytes_per_sec = int(record_num * record_size / delta)

    return result


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with open("/results/python.csv", "w") as f:
        for record_size in RECORD_SIZES:
            result = loop.run_until_complete(bench(record_size, RECORD_NUM))
            print(result)
            f.write(result.to_csv() + "\n")
