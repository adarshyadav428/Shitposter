from __future__ import annotations


def estimate_monthly_cost(posts: int, avg_input_tokens: int, avg_output_tokens: int) -> dict[str, float]:
    # Placeholder rates for planning only; replace with live vendor rates.
    input_rate_per_million = 1.0
    output_rate_per_million = 5.0
    input_cost = (posts * avg_input_tokens / 1_000_000) * input_rate_per_million
    output_cost = (posts * avg_output_tokens / 1_000_000) * output_rate_per_million
    return {
        "input_usd": round(input_cost, 2),
        "output_usd": round(output_cost, 2),
        "total_usd": round(input_cost + output_cost, 2),
    }


if __name__ == "__main__":
    report = estimate_monthly_cost(posts=50, avg_input_tokens=1800, avg_output_tokens=220)
    print(report)
