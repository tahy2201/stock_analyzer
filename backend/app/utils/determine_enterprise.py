from typing import Optional


def determine_enterprise_status(
    name: str, sector: Optional[str], market: Optional[str]
) -> bool:
    """
    企業がエンタープライズ企業かどうかを判定
    基本的な条件で判定（後でより詳細な条件に更新可能）
    """
    # 中小企業を除外するキーワード
    exclude_keywords = [
        "投資",
        "不動産投資",
        "REIT",
        "リート",
        "ファンド",
        "投資法人",
        "投資信託",
        "ホールディングス",
        "HD",
    ]

    # 小規模企業を示すキーワード
    small_company_keywords = [
        "地域",
        "県内",
        "市内",
        "ローカル",
    ]

    # エンタープライズ企業を示すキーワード（今後の拡張用）
    # enterprise_keywords = [
    #     '株式会社', '(株)', 'Corp', 'Corporation',
    #     'Ltd', 'Limited', 'Inc', 'Incorporated',
    #     'Holdings', 'Group', 'グループ'
    # ]

    # 除外キーワードがある場合は非エンタープライズ
    for keyword in exclude_keywords:
        if keyword in name:
            return False

    # 小規模企業キーワードがある場合は非エンタープライズ
    for keyword in small_company_keywords:
        if keyword in name:
            return False

    # 市場区分による判定
    if market:
        if any(
            premium_market in market
            for premium_market in ["プライム", "Prime", "東証1部", "1部"]
        ):
            return True
        elif any(
            standard_market in market
            for standard_market in ["スタンダード", "Standard", "東証2部", "2部"]
        ):
            return True

    # 業種による判定
    if sector:
        enterprise_sectors = [
            "製造業",
            "情報・通信業",
            "電気・ガス業",
            "運輸・郵便業",
            "卸売・小売業",
            "金融・保険業",
            "建設業",
            "医薬品",
            "化学",
            "機械",
            "電気機器",
            "輸送用機器",
            "精密機器",
        ]
        for enterprise_sector in enterprise_sectors:
            if enterprise_sector in sector:
                return True

    # デフォルトでは True（保守的な判定）
    return True
