import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mtick
import datetime as dt

plt.style.use("seaborn-v0_8-whitegrid")

def plot_iv_rank_history(iv_data=None):
    """
    Simple IV history line chart similar to Groww style.
    iv_data: list of tuples (date, iv%)
    """
    if not iv_data:
        # Simulated data if not provided
        iv_data = [(dt.date.today() - dt.timedelta(days=i), 12 + np.sin(i/5)*2) for i in range(30)]

    dates = [d for d, _ in iv_data][::-1]
    ivs = [v for _, v in iv_data][::-1]

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(dates, ivs, color="#00b386", linewidth=2.5, label="IV (%)")
    ax.fill_between(dates, ivs, np.min(ivs), color="#00b386", alpha=0.15)
    ax.set_title("Implied Volatility (IV) History", fontsize=11, weight="bold")
    ax.set_ylabel("IV (%)")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(alpha=0.2)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_facecolor("#ffffff")
    plt.tight_layout()
    return fig


def plot_expected_move_chart(spot, metrics):
    """
    Expected Move Band Chart – Groww-style visualization
    """
    exp1d = metrics.get("expected_move_1d", (0, 0))[0] or 0
    exp3d = metrics.get("expected_move_3d", (0, 0))[0] or 0
    if not spot:
        spot = 0

    # Simulate 3-day projection
    days = np.arange(0, 4)
    upper = spot + np.linspace(0, exp3d, len(days))
    lower = spot - np.linspace(0, exp3d, len(days))

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(days, [spot]*len(days), color="#222222", linestyle="--", linewidth=1.2, label="Spot")

    # Fill expected move bands
    ax.fill_between(days, lower, upper, color="#00b386", alpha=0.15, label="±1σ Range")
    ax.plot(days, upper, color="#00b386", linestyle="--", linewidth=1.5)
    ax.plot(days, lower, color="#ff6b6b", linestyle="--", linewidth=1.5)

    # Add annotation of expected range
    ax.text(days[-1], upper[-1], f"↑ {int(upper[-1])}", color="#00b386", fontsize=9, va="bottom", ha="left")
    ax.text(days[-1], lower[-1], f"↓ {int(lower[-1])}", color="#ff6b6b", fontsize=9, va="top", ha="left")

    # Titles and look
    ax.set_title("Expected Move Band (±1σ)", fontsize=11, weight="bold", pad=10)
    ax.set_xlabel("Days Ahead", fontsize=9)
    ax.set_ylabel("Price (₹)", fontsize=9)
    ax.set_facecolor("#ffffff")
    ax.grid(alpha=0.2)
    ax.legend(loc="upper right", fontsize=8)
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
    plt.tight_layout()
    return fig
