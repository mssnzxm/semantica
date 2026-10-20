"""合同系统（CLM 合同全生命周期）演示数据生成器。

以业界标准合同管理系统的领域模型为蓝本，生成覆盖完整主体与关系的
测试图数据，并通过 Semantica Explorer 的 /api/import 接口导入。

主体（节点类型）:
  Company / Person / Department / Contract / Amendment /
  Project / Product / PaymentTerms / Regulation

关系（边类型）:
  party_to / signs / approves / works_for / member_of /
  belongs_to / governs / involves_product / about_project /
  amends / references_regulation / guarantees /
  follows_payment_terms / renews

用法:
  python examples/contract_system_demo_data.py            # 生成并导入
  python examples/contract_system_demo_data.py --no-upload # 仅生成 JSON
"""

from __future__ import annotations

import json
import random
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

random.seed(20261020)

API_IMPORT_URL = "http://127.0.0.1:8000/api/import"
OUTPUT_PATH = Path(__file__).with_name("contract_demo_data.json")

# ---------------------------------------------------------------------------
# 领域素材（合同系统标准主数据）
# ---------------------------------------------------------------------------

COMPANIES = [
    ("上海云启科技有限公司", "信息技术", 8000, "中国（上海）自由贸易试验区世纪大道 88 号"),
    ("北京华信数联科技股份有限公司", "信息技术", 12000, "北京市海淀区中关村软件园 3 号楼"),
    ("深圳市前海智能装备有限公司", "智能制造", 15000, "深圳市南山区前海深港合作区 6 号"),
    ("杭州矩阵数据服务有限公司", "数据服务", 3000, "杭州市余杭区未来科技城 12 幢"),
    ("广州启明贸易发展有限公司", "国际贸易", 5000, "广州市天河区珠江新城华夏路 20 号"),
    ("成都天府软件系统集成有限公司", "软件集成", 2500, "成都市高新区天府大道北段 1700 号"),
    ("武汉光谷通信设备有限公司", "通信设备", 9000, "武汉市东湖高新区光谷大道 77 号"),
    ("江苏金陵精密制造有限公司", "精密制造", 20000, "南京市江宁区苏源大道 98 号"),
    ("浙江钱塘供应链管理有限公司", "供应链管理", 4000, "杭州市钱塘新区义蓬街道 6 号街"),
    ("重庆山城建设工程有限公司", "建筑工程", 18000, "重庆市渝北区财富大道 5 号"),
    ("西安丝路新能源科技有限公司", "新能源", 10000, "西安市高新区锦业路 1 号"),
    ("青岛海滨航运物流有限公司", "航运物流", 7000, "青岛市市南区香港中路 52 号"),
    ("天津渤海化工集团", "化工", 50000, "天津市滨海新区第二大街 41 号"),
    ("长沙潇湘传媒文化有限公司", "文化传媒", 1500, "长沙市岳麓区麓谷大道 658 号"),
    ("南京紫金山电子科技有限公司", "电子科技", 6000, "南京市玄武区紫金山路 9 号"),
    ("福州闽江金融服务有限公司", "金融服务", 22000, "福州市鼓楼区五四路 128 号"),
    ("郑州中原物流仓储有限公司", "物流仓储", 3600, "郑州市郑东新区商都路 100 号"),
    ("苏州园林建筑装饰工程有限公司", "建筑装饰", 5200, "苏州市姑苏区干将西路 456 号"),
    ("昆明彩云国际贸易有限公司", "国际贸易", 2000, "昆明市官渡区春城路 289 号"),
    ("合肥科里教育科技有限公司", "教育科技", 1200, "合肥市高新区望江西路 520 号"),
]

PERSON_NAMES = [
    "李文博", "王静怡", "张启航", "刘思远", "陈慧敏", "杨志强", "赵雅婷", "黄俊杰",
    "周晓曼", "吴承泽", "徐立群", "孙梦洁", "胡建国", "朱丽华", "高天翔", "林嘉禾",
    "何雪芹", "郭润生", "马晓峰", "罗丹妮", "梁国栋", "宋雨薇", "唐明礼", "许静波",
    "韩志成", "冯雅君", "邓子豪", "曹惠芳", "彭绍辉", "肖若琳",
]

TITLES = ["总经理", "副总经理", "法务总监", "财务总监", "采购总监", "销售总监", "项目经理", "合同管理专员"]

DEPARTMENTS = [
    ("法务合规部", "合同评审、合规审查与法律风险管理"),
    ("财务部", "预算审核、付款条款评审与资金管理"),
    ("采购部", "供应商选择与采购合同签署管理"),
    ("销售部", "客户拓展与销售合同签署管理"),
    ("信息技术部", "系统建设与技术类合同管理"),
    ("人力资源部", "劳务用工类合同管理"),
    ("市场部", "市场推广类合同管理"),
    ("运营管理部", "履约跟踪与合同归档管理"),
]

CONTRACT_TEMPLATES = [
    ("产品采购合同", "采购"), ("产品销售合同", "销售"), ("软件开发服务合同", "技术服务"),
    ("设备租赁合同", "租赁"), ("保密协议", "保密"), ("劳务派遣合同", "劳务"),
    ("技术服务合同", "技术服务"), ("房屋租赁合同", "租赁"), ("货物运输合同", "物流"),
    ("市场推广服务合同", "营销服务"), ("技术开发合同", "技术开发"), ("咨询顾问合同", "咨询"),
    ("运维服务合同", "技术服务"), ("设备维护合同", "技术服务"), ("原材料采购合同", "采购"),
    ("系统集成服务合同", "技术服务"), ("广告投放合同", "营销服务"), ("培训服务合同", "服务"),
    ("仓储服务合同", "物流"), ("检测认证服务合同", "服务"), ("软件许可合同", "销售"),
    ("数据服务合同", "技术服务"), ("工程总承包合同", "工程"), ("设计咨询合同", "咨询"),
    ("融资担保合同", "金融"), ("联合研发合同", "技术开发"), ("渠道代理合同", "销售"),
    ("云资源服务合同", "技术服务"), ("供应链服务合同", "服务"), ("品牌授权合同", "销售"),
]

AMENDMENT_TITLES = [
    "价格调整补充协议", "延期履行补充协议", "变更标的规格补充协议", "增加服务范围补充协议",
    "付款计划变更补充协议", "续展期限补充协议", "保密范围扩展补充协议", "违约责任修订补充协议",
]

PROJECTS = [
    ("数字化转型项目", "企业核心业务系统全面数字化改造"),
    ("智慧园区建设项目", "园区安防、能耗与通行一体化平台建设"),
    ("ERP 系统升级项目", "ERP 平台从 8.0 迁移升级至 12.0"),
    ("海外市场拓展项目", "东南亚区域市场渠道建设"),
    ("产能扩建项目", "二期厂房与产线扩建"),
    ("数据中台建设项目", "集团级数据资产平台建设"),
    ("供应链优化项目", "仓储网络与运输路径优化"),
    ("新产品研发项目", "新一代智能终端产品研发"),
    ("品牌升级项目", "品牌视觉与传播体系升级"),
    ("区域仓储网络项目", "华中区域分仓体系建设"),
]

PRODUCTS = [
    ("ERP 软件许可", "软件许可", 450000), ("云服务器资源包", "云服务", 320000),
    ("工业机器人本体", "智能装备", 280000), ("精密数控机床", "精密制造", 860000),
    ("智能仓储货架系统", "仓储设备", 150000), ("SaaS 数据分析平台", "云服务", 98000),
    ("网络安全托管服务", "安全服务", 120000), ("干线运输服务", "物流服务", 210000),
    ("冷轧钢板（大宗）", "原材料", 390000), ("办公场地租赁", "不动产租赁", 660000),
    ("数字广告投放服务", "营销服务", 540000), ("定制开发服务", "软件开发", 480000),
    ("运维支持服务", "IT 运维", 88000), ("企业培训课程包", "培训服务", 36000),
    ("检测认证服务", "专业服务", 45000),
]

PAYMENT_TERMS = [
    ("一次性预付", "签约后 10 个工作日内一次性支付"),
    ("货到付款 30 天", "验收合格后 30 天内一次性支付"),
    ("分期付款（3 期）", "签约付 40%，交付付 40%，验收付 20%"),
    ("分期付款（4 期）", "按季度等额分四期支付"),
    ("月结 60 天", "自然月对账后 60 天电汇支付"),
    ("里程碑付款", "按项目里程碑验收分批支付"),
]

REGULATIONS = [
    ("《中华人民共和国民法典》合同编", "合同订立、效力、履行与违约责任的一般规定"),
    ("《中华人民共和国数据安全法》", "数据处理活动与数据安全义务"),
    ("《中华人民共和国个人信息保护法》", "个人信息处理的合规要求"),
    ("《中华人民共和国电子签名法》", "电子签名与电子合同的法律效力"),
    ("《中华人民共和国招标投标法》", "必须招标项目的采购程序要求"),
    ("《中华人民共和国公司法》", "公司担保与决议的效力规则"),
]

STATUS_POOL = ["已生效", "履行中", "已生效", "履行中", "履行中", "已到期", "已终止", "审批中"]
CURRENCIES = ["CNY", "CNY", "CNY", "CNY", "USD"]

APPROVAL_CHAIN = [
    ("法务初审", "法务总监", "条款合规性审查通过"),
    ("财务复审", "财务总监", "付款条款与预算审核通过"),
    ("管理层终审", "总经理", "同意签署"),
]

# ---------------------------------------------------------------------------
# 数据生成
# ---------------------------------------------------------------------------

def build_dataset() -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []

    def add_node(node_id: str, node_type: str, label: str, content: str, **props):
        nodes.append({
            "id": node_id,
            "type": node_type,
            "properties": {"label": label, "content": content, **props},
        })

    def add_edge(edge_type: str, source: str, target: str, weight: float = 1.0,
                 valid_from: str | None = None, valid_until: str | None = None, **props):
        edge = {"source": source, "target": target, "type": edge_type, "weight": weight,
                "properties": dict(props)}
        if valid_from:
            edge["valid_from"] = valid_from
        if valid_until:
            edge["valid_until"] = valid_until
        edges.append(edge)

    # --- Company ---
    for i, (name, industry, capital, address) in enumerate(COMPANIES, 1):
        add_node(
            f"company-{i:02d}", "Company", name,
            f"{name}（{industry}行业，注册资本 {capital} 万元，住所地：{address}）",
            industry=industry, registered_capital_wan=capital, address=address,
            unified_credit_code=f"91310{100 + i:05d}MA{random.randint(100000, 999999)}K",
        )

    # --- Department ---（全部隶属主体公司 company-01）
    for i, (name, duty) in enumerate(DEPARTMENTS, 1):
        dept_id = f"dept-{i:02d}"
        add_node(dept_id, "Department", name, f"{name}：{duty}", duty=duty)
        add_edge("belongs_to", dept_id, "company-01", weight=0.8)

    # --- Person ---
    person_companies = [1, 2, 3, 5, 8, 11, 15, 16]
    for i, name in enumerate(PERSON_NAMES, 1):
        person_id = f"person-{i:02d}"
        company_idx = person_companies[i % len(person_companies)]
        title = TITLES[i % len(TITLES)]
        dept_idx = (i % len(DEPARTMENTS)) + 1
        add_node(
            person_id, "Person", name,
            f"{name}，{title}，任职于 {COMPANIES[company_idx - 1][0]}",
            title=title, phone=f"138{random.randint(10000000, 99999999)}",
            email=f"{person_id}@example.com",
        )
        add_edge("works_for", person_id, f"company-{company_idx:02d}", weight=0.9, title=title)
        add_edge("member_of", person_id, f"dept-{dept_idx:02d}", weight=0.5)

    # --- PaymentTerms / Regulation / Project / Product ---
    for i, (name, desc) in enumerate(PAYMENT_TERMS, 1):
        add_node(f"payment-{i:02d}", "PaymentTerms", name, desc)
    for i, (name, desc) in enumerate(REGULATIONS, 1):
        add_node(f"regulation-{i:02d}", "Regulation", name, f"{name}：{desc}")
    for i, (name, desc) in enumerate(PROJECTS, 1):
        add_node(f"project-{i:02d}", "Project", name, f"{name}：{desc}")
    for i, (name, category, unit_price) in enumerate(PRODUCTS, 1):
        add_node(
            f"product-{i:02d}", "Product", name,
            f"{name}（{category}，标准单价 {unit_price} 元）",
            category=category, unit_price_yuan=unit_price,
        )

    # --- Contract + Amendment 及其关系 ---
    base_date = date(2022, 3, 1)
    internal_staff = [p for p in range(1, 31)]  # 本方签署/审批人池

    for i, (tpl_name, category) in enumerate(CONTRACT_TEMPLATES, 1):
        contract_id = f"contract-{i:02d}"
        sign_date = base_date + timedelta(days=random.randint(0, 1300))
        duration_days = random.choice([180, 365, 540, 730, 1095])
        end_date = sign_date + timedelta(days=duration_days)
        status = random.choice(STATUS_POOL)
        currency = random.choice(CURRENCIES)
        amount = random.randint(5, 8000)
        amount_wan = amount if currency == "CNY" else round(amount / 7.2)

        party_a = "company-01"
        party_b = random.choice([c for c in range(2, 21)])
        contractor = COMPANIES[party_b - 1][0]

        add_node(
            contract_id, "Contract", f"{contract_id.upper()}《{tpl_name}》",
            f"合同编号 HT-{sign_date.year}-{i:04d}：{COMPANIES[0][0]}与{contractor}签订的{tpl_name}，"
            f"合同金额 {amount_wan} 万{('元' if currency == 'CNY' else '美元')}，"
            f"类别「{category}」，状态「{status}」。",
            contract_no=f"HT-{sign_date.year}-{i:04d}",
            category=category, status=status,
            amount=amount_wan, currency=currency,
            sign_date=sign_date.isoformat(),
        )

        add_edge("party_to", party_a, contract_id, weight=1.0, role="甲方",
                 valid_from=sign_date.isoformat())
        add_edge("party_to", f"company-{party_b:02d}", contract_id, weight=1.0, role="乙方",
                 valid_from=sign_date.isoformat())
        if random.random() < 0.2:  # 少量三方合同
            party_c = random.choice([c for c in range(2, 21) if c != party_b])
            add_edge("party_to", f"company-{party_c:02d}", contract_id, weight=0.7, role="丙方",
                     valid_from=sign_date.isoformat())

        # 签署人（双方各一名，本方优先用内部人员池）
        signer = random.choice(internal_staff)
        add_edge("signs", f"person-{signer:02d}", contract_id, weight=0.8,
                 valid_from=sign_date.isoformat())
        # 三级审批链（approves）
        for seq, (stage, title, comment) in enumerate(APPROVAL_CHAIN, 1):
            approver = random.choice(internal_staff)
            if approver != signer:
                add_edge("approves", f"person-{approver:02d}", contract_id, weight=0.6,
                         stage=stage, sequence=seq, decision="通过", comment=comment,
                         approved_on=(sign_date - timedelta(days=seq * 3)).isoformat())
        # 归口部门
        dept_idx = random.randint(1, len(DEPARTMENTS))
        add_edge("governs", f"dept-{dept_idx:02d}", contract_id, weight=0.6)
        # 标的
        for _ in range(random.randint(1, 2)):
            product_idx = random.randint(1, len(PRODUCTS))
            add_edge("involves_product", contract_id, f"product-{product_idx:02d}",
                     weight=0.9, quantity=random.randint(1, 50))
        # 付款条款
        payment_idx = random.randint(1, len(PAYMENT_TERMS))
        add_edge("follows_payment_terms", contract_id, f"payment-{payment_idx:02d}", weight=0.5)
        # 项目（约一半合同挂项目）
        if random.random() < 0.55:
            project_idx = random.randint(1, len(PROJECTS))
            add_edge("about_project", contract_id, f"project-{project_idx:02d}", weight=0.8)
        # 法规援引
        regulation_idx = random.randint(1, len(REGULATIONS))
        add_edge("references_regulation", contract_id, f"regulation-{regulation_idx:02d}", weight=0.4)
        # 担保（约 1/3 合同有第三方担保）
        if random.random() < 0.33:
            guarantor = random.choice([c for c in range(2, 21) if c != party_b])
            add_edge("guarantees", f"company-{guarantor:02d}", contract_id, weight=0.6,
                     guarantee_type=random.choice(["连带责任保证", "一般保证", "保证金担保"]),
                     valid_from=sign_date.isoformat())

    # --- Amendment（补充协议，前 8 份合同的修订）---
    for i, amend_title in enumerate(AMENDMENT_TITLES, 1):
        amend_id = f"amendment-{i:02d}"
        target = f"contract-{i:02d}"
        amend_date = date(2024, 1, 1) + timedelta(days=random.randint(0, 700))
        add_node(
            amend_id, "Amendment", f"{amend_title}（HT-2022-{i:04d} 之补充）",
            f"针对 {target.upper()} 签订的{amend_title}，签署日期 {amend_date.isoformat()}。",
            amendment_no=f"BC-{amend_date.year}-{i:04d}",
        )
        add_edge("amends", amend_id, target, weight=1.0,
                 valid_from=amend_date.isoformat(),
                 change_summary=amend_title)
        signer = random.choice(internal_staff)
        add_edge("signs", f"person-{signer:02d}", amend_id, weight=0.8,
                 valid_from=amend_date.isoformat())
        approver = random.choice(internal_staff)
        if approver != signer:
            add_edge("approves", f"person-{approver:02d}", amend_id, weight=0.6,
                     stage="法务初审", sequence=1, decision="通过")

    # --- 续签关系（后 5 份合同与前 5 份对应）---
    for i in range(1, 6):
        add_edge("renews", f"contract-{i + 25:02d}", f"contract-{i:02d}", weight=0.7,
                 renewal_note="到期续签")

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# 导入
# ---------------------------------------------------------------------------

def upload(payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    boundary = "----semanticaContractDemoBoundary"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="contract_demo.json"\r\n'
        "Content-Type: application/json\r\n\r\n"
    ).encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    request = urllib.request.Request(
        API_IMPORT_URL,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    dataset = build_dataset()
    nodes, edges = dataset["nodes"], dataset["edges"]
    print(f"生成完成：{len(nodes)} 个节点，{len(edges)} 条关系")

    OUTPUT_PATH.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已写入 {OUTPUT_PATH}")

    if "--no-upload" in sys.argv:
        return

    try:
        result = upload(dataset)
    except Exception as exc:  # noqa: BLE001
        print(f"导入失败：{exc}")
        raise SystemExit(1) from exc
    print(f"导入结果：{json.dumps(result, ensure_ascii=False, indent=2)}")

    # 汇总各类型规模
    by_type: dict[str, int] = {}
    for node in nodes:
        by_type[node["type"]] = by_type.get(node["type"], 0) + 1
    print("节点类型分布：", json.dumps(by_type, ensure_ascii=False))
    edge_types: dict[str, int] = {}
    for edge in edges:
        edge_types[edge["type"]] = edge_types.get(edge["type"], 0) + 1
    print("关系类型分布：", json.dumps(edge_types, ensure_ascii=False))


if __name__ == "__main__":
    main()
