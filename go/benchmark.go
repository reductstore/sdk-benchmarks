package main

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"os"
	"time"

	reduct "github.com/reductstore/reduct-go"
)

const (
	RecordNum       = 2000
	MaxBatchSize    = 8_000_000
	MaxBatchRecords = 80
)

var RecordSizes = []int{1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304}

type Result struct {
	WriteReqPerSec   int
	WriteBytesPerSec int
	ReadReqPerSec    int
	ReadBytesPerSec  int
	RecordSize       int64
	RecordNum        int64
}

func (r *Result) String() string {
	return fmt.Sprintf(
		"Record size: %d KiB, Record num: %d, Write req/s: %d, Write KiB/s: %d, Read req/s: %d, Read KiB/s: %d",
		r.RecordSize/1024, r.RecordNum, r.WriteReqPerSec, r.WriteBytesPerSec/1024, r.ReadReqPerSec, r.ReadBytesPerSec/1024,
	)
}

func (r *Result) ToCSV() string {
	return fmt.Sprintf("%d,%d,%d,%d,%d,%d\n", r.RecordSize, r.RecordNum, r.WriteReqPerSec, r.WriteBytesPerSec, r.ReadReqPerSec, r.ReadBytesPerSec)
}

func bench(recordSize, recordNum int64) (*Result, error) {
	result := &Result{
		RecordSize: recordSize,
		RecordNum:  recordNum,
	}

	client := reduct.NewClient("http://reductstore:8383", reduct.ClientOptions{
		APIToken: "token",
	})

	bucketName := fmt.Sprintf("benchmark-%d", time.Now().UnixMicro())
	bucket, err := client.CreateBucket(context.Background(), bucketName, nil)
	if err != nil {
		return nil, err
	}

	recordData := bytes.Repeat([]byte("0"), int(recordSize))
	startTime := time.Now()

	batch := bucket.BeginWriteBatch(context.Background(), "go-bench")
	for i := int64(0); i < recordNum; i++ {
		batch.Add(i, recordData, "text/plain", nil)
		if batch.Size() >= MaxBatchSize || batch.RecordCount() >= MaxBatchRecords {
			if _, err := batch.Write(context.Background()); err != nil {
				return nil, err
			}
			batch.Clear()
		}
	}

	if batch.RecordCount() > 0 {
		if _, err := batch.Write(context.Background()); err != nil {
			return nil, err
		}
	}

	delta := time.Since(startTime).Seconds()
	result.WriteReqPerSec = int(float64(recordNum) / delta)
	result.WriteBytesPerSec = int(float64(recordNum*recordSize) / delta)

	startTime = time.Now()
	count := int64(0)

	queryOptions := reduct.NewQueryOptionsBuilder().
		WithStart(0).
		WithStop(recordNum).
		Build()
	query, err := bucket.Query(context.Background(), "go-bench", &queryOptions)
	if err != nil {
		return nil, err
	}

	for rec := range query.Records() {
		streamReader := rec.Stream()
		buf := make([]byte, 512000)

		for {
			n, err := streamReader.Read(buf)
			if n > 0 {
				count += int64(n)
			}
			if err == io.EOF {
				break
			} else if err != nil {
				return nil, fmt.Errorf("error reading record: %w", err)
			}
		}
	}

	if count != recordNum*recordSize {
		return nil, fmt.Errorf("read %d bytes, expected %d bytes", count, recordNum*recordSize)
	}

	delta = time.Since(startTime).Seconds()
	result.ReadReqPerSec = int(float64(recordNum) / delta)
	result.ReadBytesPerSec = int(float64(recordNum*recordSize) / delta)

	return result, nil
}

func main() {
	file, err := os.Create("/results/go.csv")
	if err != nil {
		panic(err)
	}
	defer file.Close()

	for _, recordSize := range RecordSizes {
		result, err := bench(int64(recordSize), RecordNum)
		if err != nil {
			fmt.Println("Error:", err)
			continue
		}
		fmt.Println(result)
		file.WriteString(result.ToCSV())
	}
}
