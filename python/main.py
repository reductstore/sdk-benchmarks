import asyncio
import time
from datetime import datetime
from time import sleep

from reduct import Client, Bucket, Batch

RECORD_NUM = 2000
RECORD_SIZES = [2 ** x * 1024 for x in range(13)]  # 1 KiB ~ 4 MiB

MAX_BATCH_SIZE = 8_000_000
MAX_BATCH_RECORDS = 80


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
        bucket: Bucket = await client.create_bucket(f"benchmark-{measure_time}")
        record_data = b"0" * record_size
        start_time = datetime.now()

        batch = Batch()
        for i in range(record_num):
            batch.add(i, record_data)
            if len(batch) >= MAX_BATCH_RECORDS or batch.size >= MAX_BATCH_SIZE:
                await bucket.write_batch(f"python-bench", batch)
                batch.clear()

        if len(batch) > 0:
            await bucket.write_batch("python-bench", batch)

        delta = (datetime.now() - start_time).total_seconds()
        result.write_req_per_sec = int(record_num / delta)
        result.write_bytes_per_sec = int(record_num * record_size / delta)

        start_time = datetime.now()
        count = 0
        async for record in bucket.query(
                "python-bench", start=0, stop=record_num
        ):
            async for chunk in record.read(n=16_000):
                count += len(chunk)

        if count != record_num * record_size:
            raise Exception(f"Read {count} bytes, expected {record_num * record_size} bytes.")

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
