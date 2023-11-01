use std::fmt::{Display, Formatter};
use std::io::Write;
use std::pin::pin;
use std::time::SystemTime;
use reduct_rs::{ReductClient, ReductError};
use bytes::Bytes;
use futures_util::StreamExt;

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
        .url("http://127.0.0.1:8383")
        .api_token("token")
        .build();

    let bucket = client.get_bucket("benchmark").await?;
    let record_data = Bytes::from(vec![0; record_size]);

    let start_time = std::time::Instant::now();
    let measure_time = SystemTime::now();
    for _ in 0..record_num {
        bucket.write_record("rust-bench")
            .data(record_data.clone())
            .send()
            .await?;
    }

    let delta = start_time.elapsed();
    result.write_req_per_sec = record_num as f64 / delta.as_secs_f64();
    result.write_bytes_per_sec = record_num as f64 * record_size as f64 / delta.as_secs_f64();


    let mut query = bucket.query("rust-bench").start(measure_time).limit(record_num as u64).send().await?;
    let start_time = std::time::Instant::now();

    tokio::pin!(query);
    while let Some(record) = query.next().await {
        let mut stream = record?.stream_bytes();
        while let Some(chunk) = stream.next().await {
            let _ = chunk?;
        }
    }

    let delta = start_time.elapsed();
    result.read_req_per_sec = record_num as f64 / delta.as_secs_f64();
    result.read_bytes_per_sec = record_num as f64 * record_size as f64 / delta.as_secs_f64();
    Ok(result)
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), ReductError> {
    const RECORD_NUM: usize = 1000;
    let base:i32 = 2;
    let mut file = std::fs::File::create("rust.csv")?;
    for record_size in (0..15).map(|x| base.pow(x) * 1024) {
        let result = bench(record_size as usize, RECORD_NUM).await?;
        println!("{}", result);
        file.write(format!("{}\n", result).as_bytes()).unwrap();
    }
    Ok(())
}