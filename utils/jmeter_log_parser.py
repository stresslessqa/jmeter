#!/usr/bin/env python3
import argparse
import os
import sys
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Parse JMeter JTL (CSV) and produce grouped summary.")
    parser.add_argument("jtl_file", help="Path to JMeter JTL (CSV) file")
    parser.add_argument("--output-dir", default=".", help="Directory to write results_summary.csv")
    args = parser.parse_args()

    jtl = args.jtl_file
    out_dir = args.output_dir
    os.makedirs(out_dir, exist_ok=True)
    results_path = os.path.join(out_dir, "results_summary.csv")

    print(f"Парсинг {jtl} начат...")

    # Чтение CSV; если разделитель не запятая, можно добавить delimiter=';' или autodetect
    try:
        df = pd.read_csv(jtl, low_memory=False)
    except Exception as e:
        print(f"Не удалось прочитать JTL: {e}")
        sys.exit(1)

    required_cols = {"label", "elapsed"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Файл должен содержать колонки: {required_cols}. Найдены: {list(df.columns)}")

    # Приводим elapsed к числу и отбрасываем некорректные строки
    df["elapsed"] = pd.to_numeric(df["elapsed"], errors="coerce")
    df = df.dropna(subset=["elapsed"])

    grouped = df.groupby("label", dropna=False)

    summary = grouped["elapsed"].agg(
        min_ms="min",
        median_ms="median",
        mean_ms="mean",
        max_ms="max",
        p90_ms=lambda x: x.quantile(0.90),
        p95_ms=lambda x: x.quantile(0.95),
        p99_ms=lambda x: x.quantile(0.99),
        count="count",
        under_100ms=lambda x: (x <= 100).sum(),
        under_200ms=lambda x: (x <= 200).sum(),
        under_300ms=lambda x: (x <= 300).sum(),
        under_1000ms=lambda x: (x <= 1000).sum(),
        under_4000ms=lambda x: (x <= 4000).sum(),
    )

    # Вычисляем «over» и проценты
    for t in (100, 200, 300, 1000, 4000):
        summary[f"over_{t}ms"] = summary["count"] - summary[f"under_{t}ms"]
        summary[f"over_{t}ms_pct"] = (summary[f"over_{t}ms"] / summary["count"] * 100).round(2)
        summary[f"over_{t}ms_combined"] = summary[f"over_{t}ms"].astype(int).astype(str) + " (" + summary[
            f"over_{t}ms_pct"].astype(str) + "%)"

    # Округление базовых метрик
    for c in ("mean_ms", "median_ms", "p90_ms", "p95_ms", "p99_ms"):
        summary[c] = summary[c].round(2)

    summary = summary.reset_index()

    # Оставляем и переименовываем столбцы
    summary = summary[
        [
            "label", "count", "min_ms", "median_ms", "mean_ms", "max_ms",
            "p90_ms", "p95_ms", "p99_ms",
            "over_100ms_combined", "over_200ms_combined", "over_300ms_combined",
            "over_1000ms_combined", "over_4000ms_combined",
        ]
    ]

    summary.columns = [
        "Транзакция", "Количество запросов", "Min (ms)", "Median (ms)", "Mean (ms)", "Max (ms)",
        "90%le (ms)", "95%le (ms)", "99%le (ms)", ">100 ms", ">200 ms", ">300 ms", ">1000 ms", ">4000 ms",
    ]

    summary.to_csv(results_path, index=False, encoding="utf-8")
    print("Результаты записаны в", results_path)


if __name__ == "__main__":
    main()
