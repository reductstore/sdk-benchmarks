import matplotlib.pyplot as plt
import numpy as np

SIZES = ["1K", "2K", "4K", "8K", "16K", "32K", "64K", "128K", "256K", "512K", "1M", "2M", "4M", "8M", "16M", "32M",
        "64M", "128M", "256M"]
if __name__ == "__main__":
    data = np.loadtxt("./results/python.csv", delimiter=",")
    num = data.shape[0]

    fig, axs = plt.subplots(2, 1, layout="constrained")
    axs[0].bar(SIZES[:num], data[:, 5] / (2 ** 20), label="read MiB/s")
    axs[0].bar(SIZES[:num], data[:, 3] / (2 ** 20), label="write MiB/s")
    axs[0].set_xlabel("record size (KiB)")
    axs[0].legend()

    axs[1].bar(SIZES[:num], data[:, 4], label="read req/s")
    axs[1].bar(SIZES[:num], data[:, 2], label="write req/s")
    axs[1].set_xlabel("record size (KiB)")
    axs[1].legend()

    # plt.plot(data[:, 0] // 1024, data[:, 3] , label="write MiB/s")
    # plt.plot(data[:, 0] // 1024, data[:, 5] , label="read MiB/s")
    # plt.xscale("log", base=0)

    plt.savefig("./python.png")
    plt.show()
