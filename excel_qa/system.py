"""Core logic for the Excel-based question answering system."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from dateutil.parser import parse as parse_dt
from rapidfuzz import fuzz, process


AGG_FUNCS = {
    "sum": np.sum,
    "total": np.sum,
    "جمع": np.sum,
    "میانگین": np.mean,
    "avg": np.mean,
    "mean": np.mean,
    "max": np.max,
    "حداکثر": np.max,
    "min": np.min,
    "حداقل": np.min,
    "count": lambda x: x.shape[0],
    "تعداد": lambda x: x.shape[0],
}


@dataclass
class Answer:
    """Structured answer returned by :class:`ExcelQASystem`."""

    type: str
    answer: str
    preview: List[Dict[str, Any]]
    rationale: Dict[str, Any]

    def to_json(self) -> str:
        """Return the answer as formatted JSON for debugging/CLI use."""
        return json.dumps(
            {
                "type": self.type,
                "answer": self.answer,
                "preview": self.preview,
                "rationale": self.rationale,
            },
            ensure_ascii=False,
            indent=2,
        )


def slugify(value: Any) -> str:
    """Convert any value to a slug suited for column identifiers."""

    text = str(value).strip()
    text = re.sub(r"[^\w\s\-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text.lower().replace(" ", "_")


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column names and coerce obvious numeric/datetime types."""

    normalised = df.copy()
    normalised.columns = [slugify(col) for col in normalised.columns]

    for column in normalised.columns:
        series = normalised[column]
        if series.dtype != object:
            continue

        text_series = series.astype(str).str.replace(",", "", regex=False).str.strip()
        numeric = pd.to_numeric(text_series, errors="coerce")
        if numeric.notna().sum() >= 0.5 * len(series):
            normalised[column] = numeric
            continue

        try:
            dt = pd.to_datetime(text_series, errors="coerce", dayfirst=True)
        except Exception:  # pragma: no cover - defensive
            dt = None
        if dt is not None and dt.notna().sum() >= 0.5 * len(series):
            normalised[column] = dt
        else:
            normalised[column] = text_series

    return normalised


class ExcelQASystem:
    """Question answering helper that works on top of Excel workbooks."""

    def __init__(self, path: str):
        self.book = pd.ExcelFile(path)
        self.tables: Dict[str, pd.DataFrame] = {}
        for sheet in self.book.sheet_names:
            df = self.book.parse(sheet)
            self.tables[sheet] = normalize_df(df)

        self.col_catalog: List[Tuple[str, str]] = []
        for sheet_name, frame in self.tables.items():
            for column in frame.columns:
                self.col_catalog.append((sheet_name, column))

    # ------------------------------------------------------------------
    # Helper utilities
    def _choices(self) -> List[str]:
        return [f"{sheet}::{column}" for sheet, column in self.col_catalog]

    def _find_best_column(
        self, text: str, topn: int = 3, threshold: int = 60
    ) -> List[Tuple[str, str, int]]:
        """Return candidate columns that best match *text*."""

        choices = self._choices()
        results = process.extract(text, choices, scorer=fuzz.token_set_ratio, limit=topn)
        filtered = [result for result in results if result[1] >= threshold]
        parsed: List[Tuple[str, str, int]] = []
        for match, score, _ in filtered:
            sheet, column = match.split("::", 1)
            parsed.append((sheet, column, score))
        return parsed

    def _detect_sheet(self, question: str) -> Optional[str]:
        for sheet_name in self.tables.keys():
            if sheet_name.lower() in question.lower():
                return sheet_name
        return None

    def _fuzzy_col_in_df(self, text: str, df: pd.DataFrame) -> Optional[str]:
        columns = list(df.columns)
        match = process.extractOne(text, columns, scorer=fuzz.token_set_ratio)
        if match and match[1] >= 65:
            return match[0]
        return None

    def _cast_value(self, raw: str, series: pd.Series) -> Any:
        if pd.api.types.is_numeric_dtype(series):
            value = pd.to_numeric(raw, errors="coerce")
            return value if pd.notna(value) else raw
        if pd.api.types.is_datetime64_any_dtype(series):
            try:
                return parse_dt(raw, dayfirst=True)
            except Exception:
                return raw
        return raw

    def _parse_filters(self, question: str, df: pd.DataFrame) -> List[Tuple[str, str, Any]]:
        ops_map = {
            "=": "==",
            "==": "==",
            "برابر": "==",
            "بزرگتر": ">",
            ">": ">",
            "کمتر": "<",
            "<": "<",
            ">=": ">=",
            "<=": "<=",
            "contains": "contains",
            "شامل": "contains",
            "دارای": "contains",
        }

        filters: List[Tuple[str, str, Any]] = []
        tokens = re.split(r"[,\n؛;|]+", question)
        for token in tokens:
            match = re.search(
                r"(.*?)(==|>=|<=|=|>|<|contains|شامل|دارای|برابر)(.*)",
                token,
                flags=re.IGNORECASE,
            )
            if not match:
                continue

            left, operator, right = match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
            column = self._fuzzy_col_in_df(left, df)
            if not column:
                continue

            op_std = ops_map.get(operator, "==")
            value = right.strip().strip('"').strip("'")
            value = self._cast_value(value, df[column])
            filters.append((column, op_std, value))
        return filters

    def _apply_filters(
        self, df: pd.DataFrame, filters: Sequence[Tuple[str, str, Any]]
    ) -> pd.DataFrame:
        filtered = df
        for column, operator, value in filters:
            if operator == "contains":
                filtered = filtered[
                    filtered[column].astype(str).str.contains(str(value), case=False, na=False)
                ]
                continue

            try:
                if operator == "==":
                    filtered = filtered[filtered[column] == value]
                elif operator == ">":
                    filtered = filtered[filtered[column] > value]
                elif operator == "<":
                    filtered = filtered[filtered[column] < value]
                elif operator == ">=":
                    filtered = filtered[filtered[column] >= value]
                elif operator == "<=":
                    filtered = filtered[filtered[column] <= value]
            except Exception:
                filtered = filtered[filtered[column].astype(str) == str(value)]
        return filtered

    def _detect_agg(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        agg_key = None
        for key in AGG_FUNCS.keys():
            if re.search(rf"\b{key}\b", question, flags=re.IGNORECASE):
                agg_key = key
                break
        if not agg_key:
            return None, None

        candidates = self._find_best_column(question, topn=1, threshold=60)
        target_col = candidates[0][1] if candidates else None
        return agg_key, target_col

    def _pick_sheet_for_question(self, question: str) -> str:
        candidates = self._find_best_column(question, topn=1, threshold=60)
        if candidates:
            return candidates[0][0]
        return next(iter(self.tables.keys()))

    # ------------------------------------------------------------------
    # Public API
    def answer(self, question: str) -> Answer:
        sheet = self._detect_sheet(question) or self._pick_sheet_for_question(question)
        df = self.tables[sheet]
        rationale: Dict[str, Any] = {"sheet": sheet, "steps": []}

        filters = self._parse_filters(question, df)
        if filters:
            rationale["steps"].append({"filters": filters})
            df_query = self._apply_filters(df, filters)
        else:
            df_query = df

        agg_key, target_col = self._detect_agg(question)
        if agg_key and target_col and target_col in df_query.columns:
            func = AGG_FUNCS[agg_key]
            try:
                value = func(df_query[target_col].dropna())
            except Exception as exc:  # pragma: no cover - defensive
                rationale["steps"].append({"aggregation_error": str(exc)})
            else:
                preview = df_query[[target_col]].head(5)
                rationale["steps"].append({"aggregation": agg_key, "column": target_col})
                result = value.item() if hasattr(value, "item") else value
                return Answer(
                    type="aggregation",
                    answer=str(result),
                    preview=preview.to_dict(orient="records"),
                    rationale=rationale,
                )

        best_cols = [column for _, column, _ in self._find_best_column(question, topn=3, threshold=65)
                     if column in df_query.columns]
        if best_cols:
            preview = df_query[best_cols].head(10)
            rationale["steps"].append({"lookup_cols": best_cols})
            return Answer(
                type="lookup",
                answer=f"{len(df_query)} row(s) matched. Showing {len(preview)}.",
                preview=preview.to_dict(orient="records"),
                rationale=rationale,
            )

        string_columns = [column for column in df_query.columns if df_query[column].dtype == object]
        if string_columns:
            question_text = question.strip()

            def row_score(row: pd.Series) -> int:
                texts = [str(row[column]) for column in string_columns]
                scores = [fuzz.partial_ratio(question_text, text) for text in texts if text and text != "nan"]
                return max(scores or [0])

            try:
                temp = df_query.copy()
                temp["__score__"] = temp.apply(row_score, axis=1)
                temp = temp.sort_values("__score__", ascending=False).head(10)
            except Exception:  # pragma: no cover - defensive
                temp = None
            if temp is not None:
                rationale["steps"].append({"fallback": "fuzzy_row_match"})
                return Answer(
                    type="semantic-lite",
                    answer=f"Top {len(temp)} similar rows (approximate match).",
                    preview=temp.drop(columns=["__score__"]).to_dict(orient="records"),
                    rationale=rationale,
                )

        return Answer(
            type="none",
            answer="نتیجه‌ای پیدا نشد. لطفاً نام ستون یا شرط واضح‌تری بدهید.",
            preview=[],
            rationale=rationale,
        )


__all__ = ["ExcelQASystem", "Answer", "normalize_df", "slugify"]
