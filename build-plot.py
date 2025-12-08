import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

LANGS = ["rust", "node", "python", "cpp", "go"]
SIZES = [
    "1K",
    "2K",
    "4K",
    "8K",
    "16K",
    "32K",
    "64K",
    "128K",
    "256K",
    "512K",
    "1M",
    "2M",
    "4M",
    "8M",
    "16M",
    "32M",
    "64M",
    "128M",
    "256M",
]

sns.set_theme(style="whitegrid")
sns.set_palette("Set2")


def fmt_int(n):
    """Format integer with apostrophe thousands separator: 12000 -> 12'000."""
    return f"{n:,}".replace(",", "'")


def add_value_labels(ax, bars):
    """Add rotated labels placed INSIDE the bar, ending at the bar's top."""
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            fmt_int(int(height)),
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, -3),
            rotation=90,
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=8,
            color="black",
        )


if __name__ == "__main__":
    for lang in LANGS:
        try:
            data = np.loadtxt(f"./results/{lang}.csv", delimiter=",")
            print(f"Loaded results for {lang}, shape: {data.shape}")
        except Exception as e:
            print(f"Could not load results for {lang}: {e}")
            continue
        num = data.shape[0]

        x = np.arange(num)
        width = 0.35

        fig, axs = plt.subplots(2, 1, figsize=(12, 9), layout="constrained")

        # MiB/s chart
        read_mib = data[:, 5] / (2**20)
        write_mib = data[:, 3] / (2**20)

        bars1 = axs[0].bar(x - width / 2, read_mib, width, label="Read MiB/s")
        bars2 = axs[0].bar(x + width / 2, write_mib, width, label="Write MiB/s")

        add_value_labels(axs[0], bars1)
        add_value_labels(axs[0], bars2)

        min_val = min(np.min(read_mib[read_mib > 0]), np.min(write_mib[write_mib > 0]))
        max_val = max(np.max(read_mib), np.max(write_mib))

        axs[0].set_yscale("log")
        axs[0].set_ylim(min_val * 0.3, max_val * 1.5)
        axs[0].set_xticks(x)
        axs[0].set_xticklabels(SIZES[:num])
        axs[0].set_ylabel("Throughput (MiB/s)")
        axs[0].set_xlabel("Record Size (bytes)")
        axs[0].legend()
        axs[0].grid(axis="y", linestyle="--", alpha=0.6)

        # records/s chart
        read_rps = data[:, 4]
        write_rps = data[:, 2]

        bars3 = axs[1].bar(x - width / 2, read_rps, width, label="Read records/s")
        bars4 = axs[1].bar(x + width / 2, write_rps, width, label="Write records/s")

        add_value_labels(axs[1], bars3)
        add_value_labels(axs[1], bars4)

        min_val = min(np.min(read_rps[read_rps > 0]), np.min(write_rps[write_rps > 0]))
        max_val = max(np.max(read_rps), np.max(write_rps))
        
        axs[1].set_yscale("log")
        axs[1].set_ylim(min_val * 0.3, max_val * 1.5)
        axs[1].set_xticks(x)
        axs[1].set_xticklabels(SIZES[:num])
        axs[1].set_ylabel("Records/s")
        axs[1].set_xlabel("Record Size (bytes)")
        axs[1].legend()
        axs[1].grid(axis="y", linestyle="--", alpha=0.6)

        plt.suptitle(f"{lang.capitalize()} Benchmark", fontsize=16)
        plt.savefig(f"./{lang}.png", dpi=200)
        plt.show()
