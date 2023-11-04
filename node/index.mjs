import {Client} from "reduct-js";
import {Buffer} from "buffer";
import {hrtime} from "process";
import fs from "fs";

const RECORD_NUM = 1000;
/**
 * Get current time in microsecond
 * @returns {bigint}
 */
const now_us = () => {
    const [s, ns] = hrtime();
    return BigInt(s) * 1000000n + BigInt(ns) / 1000n;
}

const bench = async (recordSize, recordNum) => {
    const result = [recordSize, recordNum]
    const client = new Client("http://reductstore:8383", {
        apiToken: "token",
    });

    const measureTime = now_us();
    const bucket = await client.getBucket("benchmark");

    let start = new Date();
    const data = Buffer.alloc(recordSize);
    for (let i = 0; i < recordNum; i++) {
        const record = await bucket.beginWrite("node-bench", now_us());
        await record.write(data);
    }

    let elapsed = (new Date() - start) / 1000;
    result.push((recordNum / elapsed));
    result.push(recordNum * recordSize / elapsed);

    start = new Date();
    let count = 0;
    for await (const record of bucket.query("node-bench", measureTime, now_us(),)) {
        const data = await record.read();
        count += data.toString().length;
    }

    if (count !== recordNum * recordSize) {
        throw new Error("Mismatched data size: " + count + " vs " + recordNum * recordSize);
    }

    elapsed = (new Date() - start) / 1000;
    result.push(recordNum / elapsed);
    result.push(recordNum * recordSize / elapsed);

    return result;
}


const main = async () => {
    const csvFile = fs.createWriteStream("/results/node.csv");
    for (let i = 0; i < 15; i++) {
        const result = (await bench(2 ** i * 1024, RECORD_NUM)).map((x) => x.toFixed(2));
        console.log(result);
        csvFile.write(result.join(",") + "\n");
    }
}

await main();