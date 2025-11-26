from __future__ import annotations

"""
Feature engineering pipeline (Phase 3.5).
"""

import json
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pandas as pd
from sklearn.preprocessing import StandardScaler

from .config import DataCollectorSettings, get_settings
from .db import PostgresClient
from .models import FeatureRow
from .utils import ensure_directory

logger = logging.getLogger(__name__)


@dataclass
class FeatureBuildResult:
    features: List[FeatureRow]
    scaler_params: Dict[str, List[float]]
    dataframe: pd.DataFrame


class FeatureBuilder:
    """
    Build ML-friendly feature vectors by merging market, sentiment, macro, and fundamental data.
    """

    def __init__(self, settings: Optional[DataCollectorSettings] = None, db: Optional[PostgresClient] = None):
        self.settings = settings or get_settings()
        self.db = db or PostgresClient(self.settings.database_url)

    async def __aenter__(self) -> "FeatureBuilder":
        await self.db.connect()
        await self.db.ensure_phase3_schema()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.db.close()

    async def _load_prices(self, symbols: Sequence[str], start: date, end: date) -> pd.DataFrame:
        query = """
        SELECT symbol, trade_date, open_price, high_price, low_price, close_price, volume
        FROM daily_prices
        WHERE symbol = ANY($1) AND trade_date BETWEEN $2 AND $3
        ORDER BY trade_date ASC
        """
        records = await self.db.fetch(query, list(symbols), start, end)
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame([dict(r) for r in records])
        df.rename(
            columns={
                "trade_date": "date",
                "open_price": "open",
                "high_price": "high",
                "low_price": "low",
                "close_price": "close",
            },
            inplace=True,
        )
        return df

    async def _load_sentiment(self, symbols: Sequence[str], start: date, end: date) -> pd.DataFrame:
        query = """
        SELECT symbol, market_date, mean_sentiment, max_sentiment, article_count
        FROM daily_sentiment
        WHERE symbol = ANY($1) AND market_date BETWEEN $2 AND $3
        """
        records = await self.db.fetch(query, list(symbols), start, end)
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame([dict(r) for r in records])
        df.rename(columns={"market_date": "date"}, inplace=True)
        return df

    async def _load_macro(self, start: date, end: date) -> pd.DataFrame:
        query = """
        SELECT metric_name, as_of_date, value
        FROM macro_indicators
        WHERE as_of_date BETWEEN $1 AND $2
        """
        records = await self.db.fetch(query, start, end)
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame([dict(r) for r in records])
        df.rename(columns={"as_of_date": "date"}, inplace=True)
        pivoted = df.pivot_table(index="date", columns="metric_name", values="value").reset_index()
        return pivoted

    async def _load_fundamentals(self, symbols: Sequence[str]) -> pd.DataFrame:
        query = """
        SELECT symbol, period_end, pe, eps, roe, revenue, profit, market_cap
        FROM fundamentals
        WHERE symbol = ANY($1)
        """
        records = await self.db.fetch(query, list(symbols))
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame([dict(r) for r in records])
        df.rename(columns={"period_end": "date"}, inplace=True)
        return df

    @staticmethod
    def _compute_market_features(prices: pd.DataFrame) -> pd.DataFrame:
        if prices.empty:
            return prices

        prices = prices.sort_values(["symbol", "date"])
        grouped = prices.groupby("symbol")
        prices["return_1d"] = grouped["close"].pct_change()
        prices["return_5d"] = grouped["close"].pct_change(periods=5)
        prices["volatility_10d"] = grouped["close"].pct_change().rolling(10).std()
        prices["ma_5"] = grouped["close"].rolling(window=5, min_periods=3).mean()
        prices["ma_20"] = grouped["close"].rolling(window=20, min_periods=10).mean()
        prices["future_return_5d"] = grouped["close"].pct_change(periods=5).shift(-5)
        return prices

    @staticmethod
    def _merge_sentiment(features: pd.DataFrame, sentiment: pd.DataFrame) -> pd.DataFrame:
        if features.empty or sentiment.empty:
            return features
        sentiment = sentiment.rename(
            columns={
                "mean_sentiment": "sentiment_mean",
                "max_sentiment": "sentiment_max",
                "article_count": "sentiment_count",
            }
        )
        return features.merge(sentiment, on=["symbol", "date"], how="left")

    @staticmethod
    def _merge_macro(features: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
        if features.empty or macro.empty:
            return features
        return features.merge(macro, on="date", how="left")

    @staticmethod
    def _merge_fundamentals(features: pd.DataFrame, fundamentals: pd.DataFrame) -> pd.DataFrame:
        if features.empty or fundamentals.empty:
            return features

        merged_frames: List[pd.DataFrame] = []
        for symbol, symbol_df in features.groupby("symbol"):
            symbol_feats = symbol_df.sort_values("date")
            symbol_fund = fundamentals[fundamentals["symbol"] == symbol].sort_values("date")
            if symbol_fund.empty:
                merged_frames.append(symbol_feats)
                continue
            merged = pd.merge_asof(
                symbol_feats,
                symbol_fund,
                on="date",
                by="symbol",
                direction="backward",
                allow_exact_matches=True,
            )
            merged_frames.append(merged)
        return pd.concat(merged_frames, ignore_index=True)

    @staticmethod
    def _normalize_features(df: pd.DataFrame, feature_cols: Sequence[str]) -> tuple[pd.DataFrame, Dict[str, List[float]]]:
        if df.empty:
            return df, {"mean": [], "scale": [], "features": list(feature_cols)}

        scaler = StandardScaler()
        filled = df[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(method="ffill").fillna(0.0)
        scaled = scaler.fit_transform(filled)
        norm_cols = [f"norm_{col}" for col in feature_cols]
        df_norm = df.copy()
        for col, values in zip(norm_cols, scaled.T):
            df_norm[col] = values

        params = {"mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(), "features": list(feature_cols)}
        return df_norm, params

    @staticmethod
    def _to_feature_rows(df: pd.DataFrame, version: str) -> List[FeatureRow]:
        if df.empty:
            return []

        feature_rows: List[FeatureRow] = []
        norm_cols = [col for col in df.columns if col.startswith("norm_")]
        base_cols = [
            "return_1d",
            "return_5d",
            "volatility_10d",
            "ma_5",
            "ma_20",
            "volume",
            "sentiment_mean",
            "sentiment_count",
        ]
        macro_cols = [col for col in df.columns if col not in base_cols + norm_cols + ["symbol", "date", "close", "open", "high", "low", "future_return_5d"]]
        feature_cols = base_cols + norm_cols + macro_cols

        for _, row in df.iterrows():
            feature_vector: Dict[str, float] = {}
            for col in feature_cols:
                value = row.get(col)
                if pd.notnull(value):
                    feature_vector[col] = float(value)

            label = float(row["future_return_5d"]) if pd.notnull(row.get("future_return_5d")) else None
            feature_rows.append(
                FeatureRow(
                    symbol=row["symbol"],
                    as_of_date=row["date"],
                    version=version,
                    feature_vector=feature_vector,
                    label=label,
                )
            )
        return feature_rows

    async def _persist_features(self, rows: Sequence[FeatureRow]) -> None:
        if not rows:
            return

        query = """
        INSERT INTO features (
            symbol, as_of_date, version, feature_vector, label, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, NOW()
        )
        ON CONFLICT (symbol, as_of_date, version)
        DO UPDATE SET
            feature_vector = EXCLUDED.feature_vector,
            label = EXCLUDED.label
        """
        params = [
            (row.symbol, row.as_of_date, row.version, row.feature_vector, row.label) for row in rows
        ]
        await self.db.executemany(query, params)
        logger.info("Persisted %s feature rows", len(rows))

    def _write_parquet(self, df: pd.DataFrame, params: Dict[str, List[float]], start: date, end: date) -> Path:
        ensure_directory(self.settings.feature_output_dir)
        base = Path(self.settings.feature_output_dir)
        feature_path = base / f"features_{start}_{end}_{self.settings.feature_version}.parquet"
        params_path = base / f"scaler_{self.settings.feature_version}.json"
        df.to_parquet(feature_path, index=False)
        params_path.write_text(json.dumps(params, indent=2), encoding="utf-8")
        logger.info("Wrote features to %s and scaler params to %s", feature_path, params_path)
        return feature_path

    async def build(
        self,
        symbols: Sequence[str],
        start: date,
        end: date,
        persist_to_db: bool = True,
        write_parquet: bool = True,
    ) -> FeatureBuildResult:
        prices = await self._load_prices(symbols, start, end)
        sentiment = await self._load_sentiment(symbols, start, end)
        macro = await self._load_macro(start, end)
        fundamentals = await self._load_fundamentals(symbols)

        market_features = self._compute_market_features(prices)
        merged = self._merge_sentiment(market_features, sentiment)
        merged = self._merge_macro(merged, macro)
        merged = self._merge_fundamentals(merged, fundamentals)

        feature_cols = [
            "return_1d",
            "return_5d",
            "volatility_10d",
            "ma_5",
            "ma_20",
            "volume",
            "sentiment_mean",
            "sentiment_count",
        ]
        for col in feature_cols:
            if col not in merged.columns:
                merged[col] = pd.NA
        merged_norm, scaler_params = self._normalize_features(merged, feature_cols)
        feature_rows = self._to_feature_rows(merged_norm, version=self.settings.feature_version)

        if persist_to_db:
            await self._persist_features(feature_rows)

        if write_parquet:
            self._write_parquet(merged_norm, scaler_params, start, end)

        return FeatureBuildResult(features=feature_rows, scaler_params=scaler_params, dataframe=merged_norm)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    start = date.today() - timedelta(days=120)
    end = date.today()
    async with FeatureBuilder(settings=settings) as builder:
        await builder.build(symbols=settings.default_symbols, start=start, end=end)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
