import matplotlib.pyplot as plt
import json, os

def plot_iv_rank_history():
    """Plots VIX vs ATM IV history safely."""
    fig, ax = plt.subplots()
    path = os.path.join("data", "iv_history.json")
    if os.path.exists(path):
        try:
            hist = json.load(open(path, "r"))
            vix_vals = hist.get("vix", [])
            iv_vals = hist.get("atm_iv", [])
            if len(vix_vals) > 0 and len(iv_vals) > 0:
                x = list(range(1, max(len(vix_vals), len(iv_vals)) + 1))
                ax.plot(x[:len(vix_vals)], vix_vals, label="India VIX")
                ax.plot(x[:len(iv_vals)], iv_vals, label="ATM IV (%)")
                ax.legend()
            else:
                ax.text(0.5, 0.5, "No IV history yet", ha="center", va="center")
            ax.set_title("IV History (rolling)")
            ax.set_xlabel("Observations")
            ax.set_ylabel("Value")
        except Exception as e:
            ax.text(0.5, 0.5, f"Error loading data: {e}", ha="center", va="center")
    else:
        ax.text(0.5, 0.5, "IV history file missing", ha="center", va="center")
    return fig


def plot_expected_move_chart(spot, metrics):
    """Plots expected move bands safely."""
    fig, ax = plt.subplots()
    try:
        em1 = metrics.get("expected_move_1d", (None, None))[0]
        em3 = metrics.get("expected_move_3d", (None, None))[0]
        if spot and em1 and em3:
            xs = ["Spot-EM1", "Spot", "Spot+EM1", "Spot-EM3", "Spot+EM3"]
            ys = [spot - em1, spot, spot + em1, spot - em3, spot + em3]
            ax.plot(range(len(xs)), ys, marker="o")
            ax.set_xticks(range(len(xs)))
            ax.set_xticklabels(xs, rotation=15)
            ax.set_title("Expected Move Bands")
            ax.set_ylabel("Index Level")
        else:
            ax.text(0.5, 0.5, "Insufficient data for expected move", ha="center", va="center")
            ax.set_title("Expected Move")
    except Exception as e:
        ax.text(0.5, 0.5, f"Plot error: {e}", ha="center", va="center")
    return fig
