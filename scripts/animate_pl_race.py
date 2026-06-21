"""Generate an animated GIF of the 2023/24 Premier League title race.

Shows cumulative points week by week for the top 6 finishers, ending with
a "Manchester City Champions" annotation. Output lands in data/processed/.

Run from the project root:
    python scripts/animate_pl_race.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STANDINGS_PATH = PROJECT_ROOT / "data" / "processed" / "fct_standings_by_matchday.parquet"
TEAMS_PATH     = PROJECT_ROOT / "data" / "processed" / "dim_teams.parquet"
OUTPUT_PATH    = PROJECT_ROOT / "data" / "processed" / "pl_race_2023.gif"

PL_SEASON_ID = 1564  # 2023/24 Premier League

# Premier League team colours (hex)
TEAM_COLOURS: dict[str, str] = {
    "Manchester City FC":    "#6CABDD",
    "Arsenal FC":            "#EF0107",
    "Liverpool FC":          "#C8102E",
    "Aston Villa FC":        "#95BFE5",
    "Tottenham Hotspur FC":  "#FFFFFF",
    "Chelsea FC":            "#034694",
}

# Dark background palette
BG_COLOUR   = "#0d1117"
GRID_COLOUR = "#21262d"
TEXT_COLOUR = "#e6edf3"
DIM_COLOUR  = "#484f58"

FRAMES_AFTER_END = 40   # extra frames to hold on the final scene


# ---------------------------------------------------------------------------
# Data prep
# ---------------------------------------------------------------------------

def load_data() -> tuple[pd.DataFrame, list[str]]:
    standings = pd.read_parquet(STANDINGS_PATH)
    teams     = pd.read_parquet(TEAMS_PATH)

    pl = (
        standings[
            (standings["competition_code"] == "PL") &
            (standings["season_id"] == PL_SEASON_ID)
        ]
        .merge(teams[["team_id", "name"]], on="team_id")
    )

    # Pivot: rows = matchday, columns = team name, values = cumulative_points
    pivot = (
        pl.pivot_table(index="matchday", columns="name",
                       values="cumulative_points", aggfunc="max")
        .sort_index()
    )

    # Top-6 finishers (by points at last matchday)
    top6 = pivot.iloc[-1].nlargest(6).index.tolist()
    pivot = pivot[top6].ffill().fillna(0)

    return pivot, top6


# ---------------------------------------------------------------------------
# Animation
# ---------------------------------------------------------------------------

def build_animation(pivot: pd.DataFrame, top6: list[str]) -> animation.FuncAnimation:
    matchdays  = pivot.index.tolist()
    n_matchdays = len(matchdays)
    total_frames = n_matchdays + FRAMES_AFTER_END

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(BG_COLOUR)
    ax.set_facecolor(BG_COLOUR)

    # Static styling
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID_COLOUR)
    ax.tick_params(colors=TEXT_COLOUR, labelsize=10)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.grid(axis="y", color=GRID_COLOUR, linewidth=0.8, zorder=0)
    ax.set_xlim(1, n_matchdays)
    ax.set_ylim(0, pivot.values.max() + 8)
    ax.set_xlabel("Game Week", color=TEXT_COLOUR, fontsize=11, labelpad=8)
    ax.set_ylabel("Cumulative Points", color=TEXT_COLOUR, fontsize=11, labelpad=8)
    ax.set_title("2023 / 24  ·  Premier League  ·  Title Race",
                 color=TEXT_COLOUR, fontsize=15, fontweight="bold", pad=16)

    colours = [TEAM_COLOURS.get(t, DIM_COLOUR) for t in top6]

    # Pre-create line + dot + label objects for each team
    lines  = [ax.plot([], [], lw=2.5, color=c, zorder=3)[0] for c in colours]
    dots   = [ax.plot([], [], "o", ms=7, color=c, zorder=4)[0] for c in colours]
    labels = [
        ax.text(0, 0, t.replace(" FC", ""), color=c,
                fontsize=9, fontweight="bold", va="center", zorder=5)
        for t, c in zip(top6, colours)
    ]

    champion_text = ax.text(
        0.5, 0.5, "", transform=ax.transAxes,
        color="#FFD700", fontsize=20, fontweight="bold",
        ha="center", va="center", alpha=0,
        bbox=dict(boxstyle="round,pad=0.4", facecolor=BG_COLOUR,
                  edgecolor="#FFD700", linewidth=2),
        zorder=10,
    )

    gw_label = ax.text(
        0.97, 0.05, "", transform=ax.transAxes,
        color=DIM_COLOUR, fontsize=28, fontweight="bold",
        ha="right", va="bottom", zorder=5,
    )

    def update(frame: int):
        md_idx = min(frame, n_matchdays - 1)
        visible_mds = matchdays[: md_idx + 1]

        for i, team in enumerate(top6):
            pts = pivot.loc[visible_mds, team].values
            xs  = visible_mds

            lines[i].set_data(xs, pts)
            dots[i].set_data([xs[-1]], [pts[-1]])
            labels[i].set_position((xs[-1] + 0.3, pts[-1]))

        gw_label.set_text(f"GW {matchdays[md_idx]:02d}")

        # Reveal champion annotation during hold frames
        if frame >= n_matchdays:
            alpha = min(1.0, (frame - n_matchdays) / 10)
            champion_text.set_text("Manchester City\n*** CHAMPIONS ***")
            champion_text.set_alpha(alpha)

        return lines + dots + labels + [champion_text, gw_label]

    ani = animation.FuncAnimation(
        fig, update,
        frames=total_frames,
        interval=120,
        blit=True,
    )
    return ani


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading data...")
    pivot, top6 = load_data()
    print(f"Teams: {', '.join(top6)}")

    print("Building animation...")
    ani = build_animation(pivot, top6)

    print(f"Saving GIF -> {OUTPUT_PATH}")
    ani.save(
        OUTPUT_PATH,
        writer=animation.PillowWriter(fps=10),
        dpi=120,
    )
    print("Done.")


if __name__ == "__main__":
    main()
