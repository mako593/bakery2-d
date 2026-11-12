
import csv
import json
from pathlib import Path

from fastmcp import FastMCP


# ============================================
# MCPサーバー設定
# ============================================

mcp = FastMCP("Komugino Bakery Research")

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "bakery.csv"

REQUIRED_COLUMNS = [
    "店舗名",
    "開業日",
    "住所",
    "店舗説明",
]


# ============================================
# CSV読み込み
# ============================================

def load_bakeries():
    """
    bakery.csvから店舗情報を読み込む。

    店舗説明は分割・要約・補完せず、
    一つの文章として保持する。
    """

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSVファイルが見つかりません: {CSV_PATH}"
        )

    bakeries = []

    with CSV_PATH.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                "CSVのヘッダーがありません。"
            )

        missing_columns = [
            column
            for column in REQUIRED_COLUMNS
            if column not in reader.fieldnames
        ]

        if missing_columns:
            raise ValueError(
                f"CSVに必要な列がありません: {missing_columns}"
            )

        for row in reader:

            if not row.get("店舗名"):
                continue

            bakery = {}

            for column in REQUIRED_COLUMNS:

                value = row.get(column, "")

                bakery[column] = (
                    value.strip()
                    if isinstance(value, str)
                    else ""
                )

            bakeries.append(bakery)

    return bakeries


# ============================================
# JSON変換
# ============================================

def to_json(data):
    """
    日本語を維持してJSON文字列に変換する。
    """

    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )


# ============================================
# ツール1：店舗一覧
# ============================================

@mcp.tool()
def list_bakeries() -> str:
    """
    架空地域「こむぎ県こむぎ野区」に
    登録された全ベーカリーの
    店舗名、開業日、住所を取得する。
    """

    bakeries = load_bakeries()

    results = [
        {
            "店舗名": bakery["店舗名"],
            "開業日": bakery["開業日"],
            "住所": bakery["住所"],
        }
        for bakery in bakeries
    ]

    return to_json({
        "店舗数": len(results),
        "店舗一覧": results,
    })


# ============================================
# ツール2：指定店舗の情報取得
# ============================================

@mcp.tool()
def get_bakery(name: str) -> str:
    """
    指定された店舗名と完全一致する
    ベーカリーの登録情報を取得する。

    Args:
        name: 店舗名（例：ベーカリー1）
    """

    bakeries = load_bakeries()

    for bakery in bakeries:

        if bakery["店舗名"] == name:

            return to_json(bakery)

    return to_json({
        "検索店舗名": name,
        "結果": "該当する店舗は登録されていません。",
    })


# ============================================
# ツール3：キーワード検索
# ============================================

@mcp.tool()
def search_bakeries(keyword: str) -> str:
    """
    店舗名、住所、店舗説明から
    指定キーワードを検索する。

    店舗説明は一つの文章として扱い、
    属性ごとの分解は行わない。

    検索方法は部分文字列一致。

    Args:
        keyword: 検索キーワード
    """

    bakeries = load_bakeries()

    keyword = keyword.strip().casefold()

    if not keyword:

        return to_json({
            "結果": "検索キーワードを指定してください。"
        })

    results = []

    for bakery in bakeries:

        searchable_text = " ".join([
            bakery["店舗名"],
            bakery["住所"],
            bakery["店舗説明"],
        ]).casefold()

        if keyword in searchable_text:

            results.append(bakery)

    return to_json({
        "検索キーワード": keyword,
        "該当店舗数": len(results),
        "検索結果": results,
    })


# ============================================
# ツール4：全店舗の詳細情報
# ============================================

@mcp.tool()
def get_all_bakeries() -> str:
    """
    全30店舗の情報を取得する。

    店舗説明はCSVに記載された
    一つの文章として、そのまま返す。
    """

    bakeries = load_bakeries()

    return to_json({
        "店舗数": len(bakeries),
        "店舗情報": bakeries,
    })


# ============================================
# サーバー起動
# ============================================

if __name__ == "__main__":
    import os

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
