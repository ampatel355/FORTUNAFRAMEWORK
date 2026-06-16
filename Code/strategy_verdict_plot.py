"""Create a plain current-run skill-vs-luck summary table for the active ticker."""

from __future__ import annotations

import math
import os
import textwrap

import matplotlib.pyplot as plt
import pandas as pd

from plot_config import (
    BACKGROUND_COLOR,
    GRID_COLOR,
    SUBTITLE_SIZE,
    TEXT_COLOR,
    TITLE_SIZE,
    add_figure_caption,
    format_agent_name,
    lighten_color,
    save_chart,
    show_chart,
)

try:
    from strategy_verdicts import EVIDENCE_COLORS, VERDICT_COLORS, load_strategy_verdicts
except ModuleNotFoundError:
    from Code.strategy_verdicts import EVIDENCE_COLORS, VERDICT_COLORS, load_strategy_verdicts


ticker = os.environ.get("TICKER", "SPY")
TABLE_BBOX = [0.03, 0.19, 0.94, 0.61]
HEADER_FONT_SIZE = 7.1
BODY_FONT_SIZE = 6.9


def format_numeric_or_na(value, decimals: int) -> str:
    """Format numeric table values while keeping missing entries explicit."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "n/a"

    if math.isnan(numeric_value):
        return "n/a"

    return f"{numeric_value:.{decimals}f}"


def wrap_cell_text(text: str, width: int) -> str:
    """Wrap one cell so the full label stays visible inside the table."""
    value = str(text).strip()
    return textwrap.fill(
        value,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )


def line_count(text: str) -> int:
    """Return the number of wrapped lines in one cell."""
    return max(1, str(text).count("\n") + 1)


def apply_table_heights(
    table,
    wrapped_rows: list[list[str]],
    *,
    bbox_height: float,
    column_count: int,
) -> None:
    """Scale row heights so wrapped text fits inside the fixed table area."""
    row_heights = [0.080]
    for row in wrapped_rows:
        max_lines = max(line_count(cell_text) for cell_text in row)
        row_heights.append(0.060 + (max_lines - 1) * 0.022)

    total_height = sum(row_heights)
    scale = bbox_height / total_height if total_height > 0 else 1.0
    scaled_heights = [height * scale for height in row_heights]

    for row_index, row_height in enumerate(scaled_heights):
        for cell_index in range(column_count):
            table[row_index, cell_index].set_height(row_height)


def build_wrapped_rows(verdict_df: pd.DataFrame, wrap_widths: list[int]) -> list[list[str]]:
    """Build wrapped row text for the summary table."""
    wrapped_rows: list[list[str]] = []
    for _, row in verdict_df.iterrows():
        p_value_value = pd.to_numeric(pd.Series([row["reference_p_value"]]), errors="coerce").iloc[0]
        prominence_text = "n/a"
        if pd.notna(p_value_value):
            prominence_text = f"{(-math.log10(max(float(p_value_value), 1e-12))):.2f}"

        row_values = [
            format_agent_name(str(row["agent"]), short=True),
            str(row["evidence_label"]),
            str(row["verdict_label"]),
            str(row["confidence_label"]),
            format_numeric_or_na(p_value_value, 3),
            prominence_text,
            format_numeric_or_na(row["reference_percentile"], 1),
            format_numeric_or_na(row["reference_rcsi_z"], 2),
        ]
        wrapped_rows.append(
            [wrap_cell_text(value, width) for value, width in zip(row_values, wrap_widths)]
        )
    return wrapped_rows


def classify_row_colors(row: pd.Series) -> tuple[str, str, str]:
    """Return subtle row, evidence, and verdict colors for one table row."""
    evidence_bucket = str(row.get("evidence_bucket", "")).strip().lower()
    verdict_bucket = str(row.get("skill_luck_verdict", "")).strip().lower()
    evidence_color = EVIDENCE_COLORS.get(evidence_bucket, TEXT_COLOR)
    verdict_color = VERDICT_COLORS.get(verdict_bucket, evidence_color)
    row_color = verdict_color if verdict_bucket else evidence_color
    return row_color, evidence_color, verdict_color


def draw_table(ax, verdict_df: pd.DataFrame) -> None:
    """Draw a plain wrapped summary table with minimal styling."""
    headers = [
        "Strategy",
        "Classification",
        "Verdict",
        "Confidence",
        "p-value",
        "Prominence",
        "Percentile",
        "RCSI_z",
    ]
    col_widths = [0.20, 0.20, 0.14, 0.12, 0.09, 0.10, 0.09, 0.06]
    wrap_widths = [18, 18, 14, 12, 8, 10, 10, 8]
    alignments = ["left", "left", "left", "left", "center", "center", "center", "center"]

    wrapped_rows = build_wrapped_rows(verdict_df, wrap_widths)
    table = ax.table(
        cellText=wrapped_rows,
        colLabels=headers,
        colLoc="center",
        cellLoc="left",
        colWidths=col_widths,
        bbox=TABLE_BBOX,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(BODY_FONT_SIZE)
    apply_table_heights(
        table,
        wrapped_rows,
        bbox_height=TABLE_BBOX[3],
        column_count=len(headers),
    )

    row_colors = [classify_row_colors(row) for _, row in verdict_df.iterrows()]

    for (row_index, cell_index), cell in table.get_celld().items():
        cell.set_edgecolor(GRID_COLOR)
        cell.set_linewidth(0.6)
        cell.PAD = 0.03
        cell.get_text().set_color(TEXT_COLOR)
        cell.get_text().set_fontweight("normal")
        cell.get_text().set_linespacing(1.08)
        if row_index == 0:
            cell.set_facecolor("#F2F2F2")
            cell.get_text().set_fontsize(HEADER_FONT_SIZE)
            cell.get_text().set_ha("center")
        else:
            row_color, _, _ = row_colors[row_index - 1]
            cell.set_facecolor(lighten_color(row_color, amount=0.94))
            cell.get_text().set_fontsize(BODY_FONT_SIZE)
            cell.get_text().set_ha(alignments[cell_index])
            cell.get_text().set_va("center")

    for row_index, (row_color, evidence_color, verdict_color) in enumerate(row_colors, start=1):
        evidence_cell = table[row_index, 1]
        verdict_cell = table[row_index, 2]
        strategy_cell = table[row_index, 0]
        evidence_cell.set_facecolor(lighten_color(evidence_color, amount=0.88))
        verdict_cell.set_facecolor(lighten_color(verdict_color, amount=0.88))
        strategy_cell.set_facecolor(lighten_color(row_color, amount=0.91))
        evidence_cell.get_text().set_color(evidence_color)
        verdict_cell.get_text().set_color(verdict_color)


def main() -> None:
    """Create and save the skill-vs-luck summary chart."""
    output_filename = f"{ticker}_skill_luck_summary.png"
    verdict_df = load_strategy_verdicts(ticker)

    fig, ax = plt.subplots(figsize=(8.8, 6.9))
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.axis("off")

    ax.text(
        0.03,
        0.955,
        f"{ticker}: Skill vs Luck Summary",
        transform=ax.transAxes,
        fontsize=TITLE_SIZE,
        fontweight="normal",
        color=TEXT_COLOR,
        ha="left",
        va="top",
    )
    ax.text(
        0.03,
        0.905,
        "Current-run summary using p-value, percentile, and RCSI_z.",
        transform=ax.transAxes,
        fontsize=SUBTITLE_SIZE,
        color="#4B5563",
        ha="left",
        va="top",
    )

    draw_table(ax, verdict_df)

    add_figure_caption(
        fig,
        (
            "Prominence is reported as -log10(p). "
            "This table uses the current run's classifier-aligned p-value, percentile, and RCSI_z outputs."
        ),
    )
    save_chart(fig, output_filename)
    show_chart()


if __name__ == "__main__":
    main()
