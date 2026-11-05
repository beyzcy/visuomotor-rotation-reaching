import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CX, CY = 500, 400          # start position (center of the 1000x800 window)
trials = pd.read_csv("data/trials_20261104_152500.csv")
samples = pd.read_csv("data/samples_20261104_152500.csv")

def wrap(a):
    """Wrap an angle to [-180, 180)."""
    return (a + 180) % 360 - 180

def initial_direction_error(df_trial, target_angle, dist=60):
    """Angle between the cursor's direction when it first passes `dist` px and the target direction."""
    d = np.hypot(df_trial.cursor_x - CX, df_trial.cursor_y - CY)
    first = df_trial[d > dist]
    if first.empty:
        return np.nan
    row = first.iloc[0]
    move_angle = np.degrees(np.arctan2(-(row.cursor_y - CY), row.cursor_x - CX))  # screen y points down
    return wrap(move_angle - target_angle)

trials["ide"] = [
    initial_direction_error(samples[samples.trial == t.trial], t.target_angle_deg)
    for t in trials.itertuples()
]

colors = {"baseline": "gray", "rotation": "tab:blue", "washout": "tab:orange"}
fig, ax = plt.subplots(figsize=(10, 4))
for phase, g in trials.groupby("phase", sort=False):
    ax.scatter(g.trial, g.ide, s=12, color=colors[phase], label=phase)
ax.axhline(0, color="black", lw=0.8)
ax.set_xlabel("Trial")
ax.set_ylabel("Initial direction error (deg)")
ax.legend()
plt.tight_layout()
plt.savefig("learning_curve.png", dpi=150)
# plt.show()
print(trials.groupby("phase", sort=False).ide.agg(["count", "mean", "std"]).round(1))
for p in ["rotation", "washout"]:
    g = trials[trials.phase == p].ide
    print(p, "first 5 mean:", round(g.head(5).mean(), 1), "last 10 mean:", round(g.tail(10).mean(), 1))
