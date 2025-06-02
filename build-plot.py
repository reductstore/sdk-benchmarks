import matplotlib.pyplot as plt
import numpy as np

LANGS = ["rust", "node", "python", "cpp", "go"]
SIZES = ["1K", "2K", "4K", "8K", "16K", "32K", "64K", "128K", "256K", "512K", "1M", "2M", "4M", "8M", "16M", "32M",
        "64M", "128M", "256M"]

if __name__ == "__main__":
    for lang in LANGS:
        data = np.loadtxt(f"./results/{lang}.csv", delimiter=",")
        num = data.shape[0]

        fig, axs = plt.subplots(2, 1, layout="constrained")
        axs[0].bar(SIZES[:num], data[:, 5] / (2 ** 20), label="read MiB/s", alpha=0.8)
        axs[0].bar(SIZES[:num], data[:, 3] / (2 ** 20), label="write MiB/s", alpha=0.8)
        axs[0].set_xlabel("record size (KiB)")
        axs[0].legend()

        axs[1].bar(SIZES[:num], data[:, 4], label="read records/s", alpha=0.8)
        axs[1].bar(SIZES[:num], data[:, 2], label="write records/s", alpha=0.8)
        axs[1].set_xlabel("record size (KiB)")
        axs[1].legend()

        plt.title(f"{lang.capitalize()} benchmark")
        plt.savefig(f"./{lang}")
        plt.show()
