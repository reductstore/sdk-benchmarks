use bytes::Bytes;
use futures_util::StreamExt;
use reduct_rs::{condition, Record, ReductClient, ReductError};
use std::fmt::{Display, Formatter};
use std::io::Write;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

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
        write!(
            f,
            "{},{},{},{},{},{}",
            self.record_size,
            self.record_num,
            self.write_req_per_sec,
            self.write_bytes_per_sec,
            self.read_req_per_sec,
            self.read_bytes_per_sec
        )
    }
}

async fn bench(
    record_size: usize,
    record_num: usize,
    entry_num: usize,
) -> Result<BenchResult, ReductError> {
    let mut result = BenchResult {
        write_req_per_sec: 0.0,
        write_bytes_per_sec: 0.0,
        read_req_per_sec: 0.0,
        read_bytes_per_sec: 0.0,
        record_size,
        record_num,
    };

    let client = Arc::new(
        ReductClient::builder()
            .url("http://reductstore:8383")
            .api_token("token")
            .build(),
    );

    let bucket = client
        .create_bucket(&format!(
            "benchmark-{}",
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_millis()
        ))
        .send()
        .await?;

    let record_data = Bytes::from(vec![0; record_size]);
    let start_time = std::time::Instant::now();

    let records_per_entry = record_num / entry_num;
    let bucket_name = bucket.name().to_string();
    let mut handles = Vec::new();

    for entry_idx in 0..entry_num {
        let record_data_clone = record_data.clone();
        let bucket_name_clone = bucket_name.clone();
        let client_clone = Arc::clone(&client);
        let entry_name = format!("rust-bench-{}", entry_idx);

        let handle = tokio::spawn(async move {
            let thread_bucket = client_clone.get_bucket(&bucket_name_clone).await?;
            let mut batch = thread_bucket.write_batch(&entry_name);

            for i in 0..records_per_entry {
                batch.append_record(
                    Record::builder()
                        .data(record_data_clone.clone())
                        .timestamp_us((entry_idx * records_per_entry + i) as u64)
                        .build(),
                );

                if batch.size() >= MAX_BATCH_SIZE || batch.record_count() >= MAX_BATCH_RECORDS {
                    batch.send().await?;
                    batch = thread_bucket.write_batch(&entry_name);
                }
            }

            if batch.record_count() > 0 {
                batch.send().await?;
            }
            Ok::<(), ReductError>(())
        });
        handles.push(handle);
    }

    // Wait for all writing tasks to complete
    for handle in handles {
        handle.await.unwrap()?;
    }

    let delta = start_time.elapsed();
    result.write_req_per_sec = record_num as f64 / delta.as_secs_f64();
    result.write_bytes_per_sec = record_num as f64 * record_size as f64 / delta.as_secs_f64();

    let start_time = std::time::Instant::now();
    let mut read_handles = Vec::new();

    for entry_idx in 0..entry_num {
        let bucket_name_clone = bucket_name.clone();
        let client_clone = Arc::clone(&client);
        let entry_name = format!("rust-bench-{}", entry_idx);

        let handle = tokio::spawn(async move {
            let thread_bucket = client_clone.get_bucket(&bucket_name_clone).await?;
            let query = thread_bucket
                .query(&entry_name)
                .start_us(0)
                .when(condition!({"$limit": records_per_entry as u64}))
                .send()
                .await?;

            tokio::pin!(query);
            let mut count = 0;
            while let Some(record) = query.next().await {
                let mut stream = record?.stream_bytes();
                while let Some(chunk) = stream.next().await {
                    let chunk = chunk?;
                    count += chunk.len();
                }
            }
            Ok::<usize, ReductError>(count)
        });
        read_handles.push(handle);
    }

    let mut total_count = 0;
    for handle in read_handles {
        total_count += handle.await.unwrap()?;
    }

    assert_eq!(
        total_count,
        record_num * record_size,
        "Check read data size"
    );
    let delta = start_time.elapsed();
    result.read_req_per_sec = record_num as f64 / delta.as_secs_f64();
    result.read_bytes_per_sec = record_num as f64 * record_size as f64 / delta.as_secs_f64();
    Ok(result)
}

#[tokio::main(flavor = "multi_thread")]
async fn main() -> Result<(), ReductError> {
    const RECORD_NUM: usize = 2000;
    const ENTRY_NUM: usize = 10;
    let base: i32 = 2;
    let mut file = std::fs::File::create("/results/rust.csv")?;
    for record_size in (0..13).map(|x| base.pow(x) * 1024) {
        let result = bench(record_size as usize, RECORD_NUM, ENTRY_NUM).await?;
        println!("{}", result);
        file.write(format!("{}\n", result).as_bytes()).unwrap();
    }
    Ok(())
}
