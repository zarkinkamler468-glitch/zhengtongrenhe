"""监测源预设数据，由 scripts/build_seed_from_excel.py 从 Excel 汇总表生成。

注意：各省教育厅官网栏目路径并不统一，不能共用 /zwgk/tzgg/ 模板。
需按每个官网实际「通知公告 / 政策文件 / 政务公开」等板块单独配置 column_url。
栏目地址经 scripts/discover_column_urls.py 与人工核验后维护。
"""
from app.models.monitor import ColumnType, SourceType

MOE_SOURCE = {
    "name": "中华人民共和国教育部",
    "url": "https://www.moe.gov.cn",
    "type": SourceType.MOE,
    "columns": [
        {"column_name": "通知公告", "column_url": "https://www.moe.gov.cn/jyb_xwfb/s271/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
        {"column_name": "政策文件", "column_url": "https://www.moe.gov.cn/jyb_sjzl/s3165/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        {"column_name": "项目申报", "column_url": "https://www.moe.gov.cn/jyb_xwfb/s5984/", "column_type": ColumnType.PROJECT_APPLY, "crawl_interval": 30},
    ],
}

PROVINCIAL_SOURCES = [
    {
        "name": "北京市教育委员会",
        "url": "https://jw.beijing.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jw.beijing.gov.cn/tzgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jw.beijing.gov.cn/xxgk/2024zcwj/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "天津市教育委员会",
        "url": "https://jy.tj.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jy.tj.gov.cn/ZWGK_52172/TZGG/", "column_type": ColumnType.NOTICE, "crawl_interval": 30, "list_selector": "li a[onclick], li a[href*='t20']"},
            {"column_name": "政策文件", "column_url": "https://jy.tj.gov.cn/ZWGK_52172/zcwj/", "column_type": ColumnType.POLICY, "crawl_interval": 60, "list_selector": "li a[onclick], li a[href*='t20']"},
        ],
    },
    {
        "name": "河北省教育厅",
        "url": "https://jyt.hebei.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.hebei.gov.cn/zwgk/tzgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.hebei.gov.cn/zwgk/zcfg/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "山西省教育厅",
        "url": "https://jyt.shanxi.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.shanxi.gov.cn/xwzx/ggtz/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.shanxi.gov.cn/jgsz/jgcs/zcfgc/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "内蒙古自治区教育厅",
        "url": "https://jyt.nmg.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.nmg.gov.cn/zwgk/tzgg_25132/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.nmg.gov.cn/zfxxgk/fdzdgknr/bmwj/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "辽宁省教育厅",
        "url": "https://jyt.ln.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.ln.gov.cn/jyt/gk/gsgg/index.shtml", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/zc/xzgfxwj/index.shtml", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "吉林省教育厅",
        "url": "https://jyt.jl.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.jl.gov.cn/zwgk/ggl/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.jl.gov.cn/zwgk/zcfg/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "黑龙江省教育厅",
        "url": "https://jyt.hlj.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.hlj.gov.cn/jyt/c110481/public_list.shtml", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.hlj.gov.cn/jyt/c110487/public_zfxxgk.shtml?tab=gfxwj", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "上海市教育委员会",
        "url": "https://edu.sh.gov.cn",
        "type": SourceType.PROVINCIAL,
        "use_playwright": True,
        "columns": [
            {"column_name": "公示公告", "column_url": "https://edu.sh.gov.cn/web/gsgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://edu.sh.gov.cn/xxgk2_zhzw_zcwj_02/index.html", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "江苏省教育厅",
        "url": "https://jyt.jiangsu.gov.cn",
        "type": SourceType.PROVINCIAL,
        "use_playwright": True,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.jiangsu.gov.cn/col/col58320/index.html", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.jiangsu.gov.cn/col/col77615/index.html", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "浙江省教育厅",
        "url": "https://jyt.zj.gov.cn",
        "type": SourceType.PROVINCIAL,
        "use_playwright": True,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.zj.gov.cn/col/col1229266336/index.html", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.zj.gov.cn/col/col1229106823/index.html", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "安徽省教育厅",
        "url": "https://jyt.ah.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.ah.gov.cn/xwzx/tzgg/index.html", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.ah.gov.cn/public/column/7071?type=4&action=list&nav=3&catId=34482303", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "福建省教育厅",
        "url": "https://jyt.fujian.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.fujian.gov.cn/xxgk/gggs/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.fujian.gov.cn/xxgk/zfxxgkzl/zc/xzgfxwj/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "江西省教育厅",
        "url": "https://jyt.jiangxi.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.jiangxi.gov.cn/zwgk/tzgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.jiangxi.gov.cn/zwgk/zcfg/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "山东省教育厅",
        "url": "http://edu.shandong.gov.cn",
        "type": SourceType.PROVINCIAL,
        "use_playwright": True,
        "columns": [
            {"column_name": "通知公告", "column_url": "http://edu.shandong.gov.cn/col/col11982/index.html", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "http://edu.shandong.gov.cn/col/col11990/index.html", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "河南省教育厅",
        "url": "https://jyt.henan.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.henan.gov.cn/xxgk/gggs/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.henan.gov.cn/zwgk/zc/xzgfxwj", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "湖北省教育厅",
        "url": "https://jyt.hubei.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "http://jyt.hubei.gov.cn/zfxxgk/zc_GK2020/qtzdgkwj_GK2020/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "http://jyt.hubei.gov.cn/zfxxgk/zc_GK2020/gfxwj_GK2020/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "湖南省教育厅",
        "url": "https://jyt.hunan.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.hunan.gov.cn/zwgk/tzgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.hunan.gov.cn/zwgk/zcfg/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "广东省教育厅",
        "url": "https://edu.gd.gov.cn",
        "type": SourceType.PROVINCIAL,
        "use_playwright": True,
        "columns": [
            {"column_name": "公示公告", "column_url": "https://edu.gd.gov.cn/zwgknew/gsgg/index.html", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "教育政策法规", "column_url": "https://edu.gd.gov.cn/zwgknew/jyzcfg/index.html", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "广西壮族自治区教育厅",
        "url": "https://jyt.gxzf.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.gxzf.gov.cn/zwgk/tzgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.gxzf.gov.cn/zwgk/zcfg/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "海南省教育厅",
        "url": "https://edu.hainan.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://edu.hainan.gov.cn/zwgk/tzgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://edu.hainan.gov.cn/edu/0500/tylist.shtml?ddtab=true", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "重庆市教育委员会",
        "url": "https://jw.cq.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jw.cq.gov.cn/zwxx_209/gggs/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jw.cq.gov.cn/zwgk/zfxxgkml/zcwj/gfxwj/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
            {"column_name": "政务文件", "column_url": "https://jw.cq.gov.cn/zwgk/zfxxgkml/zcwj/qtwj/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "四川省教育厅",
        "url": "https://edu.sc.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://edu.sc.gov.cn/scedu/c100495/xwzx_list.shtml", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://edu.sc.gov.cn/scedu/c100503/xwzx_list.shtml", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "贵州省教育厅",
        "url": "https://jyt.guizhou.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.guizhou.gov.cn/zwgk/tzgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.guizhou.gov.cn/zwgk/zcjd/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "云南省教育厅",
        "url": "https://jyt.yn.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.yn.gov.cn/article/category/fb23c6e425a14040a8efbef2fa58e43f", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.yn.gov.cn/article/category/policy03", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "西藏自治区教育厅",
        "url": "https://jyt.xizang.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.xizang.gov.cn/zwgk/tzgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.xizang.gov.cn/zwgk/zcfg/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "陕西省教育厅",
        "url": "https://jyt.shaanxi.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.shaanxi.gov.cn/gk/fdnr/gsgggk/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.shaanxi.gov.cn/gk/zc/gfxwj/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "甘肃省教育厅",
        "url": "https://jyt.gansu.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.gansu.gov.cn/zwgk/tzgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.gansu.gov.cn/zwgk/zcfg/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "青海省教育厅",
        "url": "https://jyt.qinghai.gov.cn",
        "type": SourceType.PROVINCIAL,
        "use_playwright": True,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.qinghai.gov.cn/zwgk/tzgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.qinghai.gov.cn/zwgk/zcfg/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "宁夏回族自治区教育厅",
        "url": "https://jyt.nx.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.nx.gov.cn/xwdt/tzgg/", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.nx.gov.cn/zwgk/zcwj/gfxwj/", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
    {
        "name": "新疆维吾尔自治区教育厅",
        "url": "https://jyt.xinjiang.gov.cn",
        "type": SourceType.PROVINCIAL,
        "columns": [
            {"column_name": "通知公告", "column_url": "https://jyt.xinjiang.gov.cn/edu/gsgg/list_xw.shtml", "column_type": ColumnType.NOTICE, "crawl_interval": 30},
            {"column_name": "政策文件", "column_url": "https://jyt.xinjiang.gov.cn/edu/gfxwj/newzfxxgk_list2.shtml", "column_type": ColumnType.POLICY, "crawl_interval": 60},
        ],
    },
]

