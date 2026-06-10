from pydantic import BaseModel


class CountStat(BaseModel):
    today: int
    this_week: int
    this_month: int
    total: int


class IndustryStat(BaseModel):
    name: str
    count: int


class HotWordItem(BaseModel):
    keyword: str
    count: int
    trend: str = "stable"


class AnalyticsOverview(BaseModel):
    policy_stats: CountStat
    industry_stats: list[IndustryStat]
    hot_words: list[HotWordItem]
