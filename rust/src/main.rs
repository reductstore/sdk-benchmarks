use std::fmt::{Display, Formatter};
use std::io::Write;
use std::pin::pin;
use std::time::{SystemTime, UNIX_EPOCH};
use reduct_rs::{Record, ReductClient, ReductError};
use bytes::Bytes;
use futures_util::StreamExt;

const MAX_BATCH_RECORDS: usize = 90;
const MAX_BATCH_SIZE: usize = 8_000_000;

struct BenchResult {
    write_req_per_sec: f64,
    write_bytes_per_sec: f64,
    read_req_per_sec: f64,
    read_bytes_per_sec: f64,
    record_size: usize,
    record_num: usize,
}

impl Display for BenchResult {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        write!(f, "{},{},{},{},{},{}", self.record_size, self.record_num, self.write_req_per_sec, self.write_bytes_per_sec, self.read_req_per_sec, self.read_bytes_per_sec)
    }
}

async fn bench(record_size: usize, record_num: usize) -> Result<BenchResult, ReductError> {
    let mut result = BenchResult {
        write_req_per_sec: 0.0,
        write_bytes_per_sec: 0.0,
        read_req_per_sec: 0.0,
        read_bytes_per_sec: 0.0,
        record_size,
        record_num,
    };

    let client = ReductClient::builder()
        .url("http://reductstore:8383")
        .api_token("token")
        .build();

    let bucket = client.create_bucket(&format!("benchmark-{}", SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_millis())).send().await?;

    let record_data = Bytes::from(vec![0; record_size]);
    let start_time = std::time::Instant::now();
    let measure_time = SystemTime::now();

    let mut batch = bucket.write_batch("rust-bench");
    for i in 0..record_num {
        batch.append_record(Record::builder()
            .data(record_data.clone())
            .timestamp_us(i as u64)
            .build());

        if batch.size() >= MAX_BATCH_SIZE || batch.record_count() >= MAX_BATCH_RECORDS {
            batch.send().await?;
            batch = bucket.write_batch("rust-bench");
        }
    }

    if batch.record_count() > 0 {
        batch.send().await?;
    }

    let delta = start_time.elapsed();
    result.write_req_per_sec = record_num as f64 / delta.as_secs_f64();
    result.write_bytes_per_sec = record_num as f64 * record_size as f64 / delta.as_secs_f64();


    let query = bucket.query("rust-bench").start_us(0).limit(record_num as u64).send().await?;
    let start_time = std::time::Instant::now();

    tokio::pin!(query);

    let mut count = 0;
    while let Some(record) = query.next().await {
        let mut stream = record?.stream_bytes();
        while let Some(chunk) = stream.next().await {
            let chunk = chunk?;
            count += chunk.len();
        }
    }

    assert_eq!(count, record_num * record_size, "Check read data size");
    let delta = start_time.elapsed();
    result.read_req_per_sec = record_num as f64 / delta.as_secs_f64();
    result.read_bytes_per_sec = record_num as f64 * record_size as f64 / delta.as_secs_f64();
    Ok(result)
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), ReductError> {
    const RECORD_NUM: usize = 2000;
    let base:i32 = 2;
    let mut file = std::fs::File::create("/results/rust.csv")?;
    for record_size in (0..11).map(|x| base.pow(x) * 1024) {
        let result = bench(record_size as usize, RECORD_NUM).await?;
        println!("{}", result);
        file.write(format!("{}\n", result).as_bytes()).unwrap();
    }
    Ok(())
}