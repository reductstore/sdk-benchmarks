import {Client} from "reduct-js";
import {Buffer} from "buffer";

const RECORD_NUM = 1000;

const bench = async (recordSize, recordNum) => {
    const client = new Client("http://reductstore:8383", {
        apiToken: "token",
    });

    const measureTime = new Date();
    const bucket = await client.getBucket("benchmark");
    const data = Buffer.alloc(recordSize);
    for (let i = 0; i < recordNum; i++) {
        const record = await bucket.beginWrite("js-bench",
            new Date().getMilliseconds() * 1000);
        await record.write(data);
    }
}