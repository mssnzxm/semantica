"""合同系统全功能测试数据灌入脚本。

在基础合同图数据（contract_system_demo_data.py）之上，为 Semantica
所有功能模块补充测试数据，全部以合同领域为示例：

  决策工作区    type="decision" 节点 + CAUSED/INFLUENCED/PRECEDENT_FOR 因果链
  增强工作区    相似实体（供 /api/enrich/dedup 与 DiffMerge 演示）
  本体中心      /api/ontology/load 灌入合同管理本体（Turtle）
  词表浏览器    /api/vocabulary/import 灌入合同类别 SKOS 词表（Turtle）
  图谱标注      /api/annotations 为合同节点添加法务审查标注
  推理演练场    /api/reason 运行合同规则并写回推断边
  智能体记忆    生成合同审查经验记忆（AgentMemory，供记忆工作区展示）

用法（先以 SEMANTICA_AGENT_MEMORY_PATH 环境变量启动服务）:
  python examples/contract_full_feature_data.py
"""

from __future__ import annotations

import json
import mimetypes
import random
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_system_demo_data import build_dataset as build_base_dataset  # noqa: E402

random.seed(20261020)

BASE = "http://127.0.0.1:8000"
AGENT_MEMORY_DIR = Path(__file__).with_name("agent_memory_data")

# ---------------------------------------------------------------------------
# HTTP 基础
# ---------------------------------------------------------------------------


def _request(path: str, payload: dict | None = None, method: str = "GET",
             raw_body: bytes | None = None, content_type: str | None = None) -> dict:
    url = f"{BASE}{path}"
    data = raw_body
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        content_type = content_type or "application/json"
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _multipart_upload(path: str, field: str, filename: str, blob: bytes) -> dict:
    boundary = f"----semantica{uuid.uuid4().hex}"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
        f"Content-Type: {mimetypes.guess_type(filename)[0] or 'application/octet-stream'}\r\n\r\n"
    ).encode("utf-8") + blob + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def import_graph(payload: dict) -> dict:
    blob = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return _multipart_upload("/api/import", "file", "payload.json", blob)


def graph_node_count() -> int:
    return int(_request("/api/graph/nodes?limit=1")["total"])


# ---------------------------------------------------------------------------
# 1. 决策数据（决策工作区 + 因果链）
# ---------------------------------------------------------------------------


def build_decision_dataset() -> dict:
    nodes, edges = [], []

    def node(nid, label, content, **props):
        nodes.append({"id": nid, "type": "decision",
                      "properties": {"label": label, "content": content, **props}})

    def edge(etype, src, dst, weight=0.8, **props):
        edges.append({"source": src, "target": dst, "type": etype,
                      "weight": weight, "properties": dict(props)})

    decisions = [
        # id, 标题, 类别, 情景, 理由, 结论, 置信度
        ("decision-01", "批准《原材料采购合同》HT-2022-0015",
         "采购审批", "钢材价格处于年内低位，供应商报价低于市场均价 8%",
         "采购部已完成三家比价；供应商近两年履约率 100%；预算充足",
         "批准", 0.93),
        ("decision-02", "驳回《市场推广服务合同》超长账期条款",
         "条款审查", "乙方要求月结 120 天，超出公司付款政策上限",
         "付款条款超出财务制度红线，须按标准账期重谈",
         "驳回", 0.88),
        ("decision-03", "对《工程总承包合同》追加履约保证金",
         "风险控制", "承包方资产负债率高于 75%，存在履约风险",
         "依据《民法典》合同编第五百八十六条，要求提交合同金额 10% 的履约保证金",
         "变更条件", 0.9),
        ("decision-04", "启用电子签署通道签署《保密协议》",
         "流程优化", "异地签署时效影响合作进度",
         "《电子签名法》确认可靠电子签名效力，SaaS 平台已通过等保三级",
         "批准", 0.95),
        ("decision-05", "终止《云资源服务合同》并启动替换",
         "供应商管理", "云服务商连续两季度可用性低于 SLA 约定",
         "触发服务等级协议中的终止条款，切换成本已在预算内",
         "终止", 0.85),
        ("decision-06", "续签《ERP 系统升级项目》框架协议",
         "续签决策", "一期交付质量达标，二期需求明确",
         "延续原供应商可降低集成风险；参考 decision-01 比价结论",
         "批准", 0.87),
        ("decision-07", "对《融资担保合同》要求股东会决议",
         "合规审查", "担保金额超过公司净资产 30%",
         "依据《公司法》第十六条，对外担保须经股东会决议",
         "补充程序", 0.96),
        ("decision-08", "批准《数据服务合同》个人信息处理条款",
         "数据合规", "服务涉及用户画像数据的外部处理",
         "已签署数据处理协议（DPA），满足《个人信息保护法》要求",
         "批准", 0.91),
        ("decision-09", "调整《劳务派遣合同》用工比例",
         "用工合规", "派遣用工占比接近 10% 红线",
         "参考历史先例 decision-03 的风险控制思路，逐步转为外包服务",
         "变更条件", 0.84),
        ("decision-10", "接受《检测认证服务合同》降价方案",
         "商务谈判", "供应商年度框架降价 5% 换取两年长约",
         "两年长约锁定价格，历史价格波动率 12%，降价方案有利",
         "批准", 0.89),
        ("decision-11", "驳回《渠道代理合同》独家条款",
         "条款审查", "独家代理限制公司在区域内自主销售",
         "参考 decision-02 的驳回先例，核心渠道能力不可让渡",
         "驳回", 0.86),
        ("decision-12", "批准《海外市场拓展项目》多币种结算",
         "财务审批", "美元结算存在汇率波动敞口",
         "叠加远期锁汇后成本可控；财务部已核定外汇额度",
         "批准", 0.83),
    ]

    for nid, label, category, scenario, reasoning, outcome, confidence in decisions:
        node(nid, label,
             f"{label}。情景：{scenario}。决策理由：{reasoning}。结论：{outcome}。",
             category=category, scenario=scenario, reasoning=reasoning,
             outcome=outcome, confidence=confidence, department="法务合规部")

    # 因果链：CAUSED（导致）/ INFLUENCED（影响）/ PRECEDENT_FOR（先例）
    causal = [
        ("CAUSED", "decision-02", "decision-06", "驳回条款促成续签时重谈付款条款"),
        ("CAUSED", "decision-05", "decision-04", "服务终止倒逼签署流程提速"),
        ("CAUSED", "decision-07", "decision-10", "合规审查延期影响年度谈判窗口"),
        ("INFLUENCED", "decision-01", "decision-06", "比价结论支撑续签决策"),
        ("INFLUENCED", "decision-03", "decision-09", "风险控制思路延伸至用工合规"),
        ("PRECEDENT_FOR", "decision-02", "decision-11", "付款条款驳回成为同类谈判先例"),
        ("PRECEDENT_FOR", "decision-03", "decision-07", "担保风控先例被合规审查援引"),
        ("PRECEDENT_FOR", "decision-08", "decision-12", "数据合规结论用于海外业务决策"),
    ]
    for etype, src, dst, note in causal:
        edge(etype, src, dst, weight=0.85, causal_note=note)

    # 决策 ↔ 合同/法规/项目 的关联边
    regards = {
        "decision-01": "contract-15", "decision-02": "contract-10",
        "decision-03": "contract-23", "decision-04": "contract-05",
        "decision-05": "contract-29", "decision-06": "contract-21",
        "decision-07": "contract-25", "decision-08": "contract-22",
        "decision-09": "contract-06", "decision-10": "contract-20",
        "decision-11": "contract-28", "decision-12": "contract-30",
    }
    for did, contract_id in regards.items():
        edge("regards", did, contract_id, weight=0.9)
    cites = {
        "decision-03": "regulation-01", "decision-04": "regulation-04",
        "decision-07": "regulation-06", "decision-08": "regulation-03",
        "decision-09": "regulation-02",
    }
    for did, reg in cites.items():
        edge("cites", did, reg, weight=0.6)
    for did in ("decision-01", "decision-06", "decision-12"):
        edge("about_project", did, "project-01", weight=0.7)

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# 2. 相似实体（实体消歧 / DiffMerge 演示）
# ---------------------------------------------------------------------------


def build_dedup_dataset() -> dict:
    nodes, edges = [], []

    variants = [
        # id, type, label, content（与既有实体高度相似）
        ("company-21", "Company", "北京华信数联科技股份有限公司",
         "北京华信数联科技股份有限公司（信息技术行业，注册资本 12000 万元，住所地：北京市海淀区中关村软件园 3 号楼）"),
        ("company-22", "Company", "华信数联",
         "华信数联（信息技术行业，注册资本 12000 万元），即北京华信数联科技股份有限公司"),
        ("company-23", "Company", "深圳市前海智能装备公司",
         "深圳市前海智能装备公司（智能制造行业，注册资本 15000 万元，住所地：深圳市南山区前海深港合作区 6 号）"),
        ("product-16", "Product", "ERP 软件授权许可",
         "ERP 软件授权许可（软件许可，标准单价 450000 元）"),
        ("product-17", "Product", "ERP 软件许可协议",
         "ERP 软件许可协议（软件许可，标准单价 450000 元）"),
    ]
    for nid, ntype, label, content in variants:
        nodes.append({"id": nid, "type": ntype,
                      "properties": {"label": label, "content": content}})

    # 让重复实体接入图（与原实体挂到同一份合同），便于消歧对比
    edges = [
        {"source": "company-21", "target": "contract-02", "type": "party_to",
         "weight": 1.0, "properties": {"role": "乙方"}},
        {"source": "company-22", "target": "contract-02", "type": "party_to",
         "weight": 1.0, "properties": {"role": "乙方"}},
        {"source": "company-23", "target": "contract-03", "type": "party_to",
         "weight": 1.0, "properties": {"role": "乙方"}},
        {"source": "contract-21", "target": "product-16", "type": "involves_product",
         "weight": 0.9, "properties": {"quantity": 10}},
        {"source": "contract-21", "target": "product-17", "type": "involves_product",
         "weight": 0.9, "properties": {"quantity": 10}},
    ]
    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# 3. 合同管理本体（本体中心）
# ---------------------------------------------------------------------------

ONTOLOGY_TTL = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix clm: <http://example.org/ontology/clm#> .

clm:contractOntology a owl:Ontology ;
    rdfs:label "合同管理本体"@zh , "Contract Management Ontology"@en ;
    rdfs:comment "合同全生命周期管理领域本体：主体、合同、审批、标的与合规"@zh ;
    owl:versionInfo "1.0" .

clm:Contract a owl:Class ; rdfs:label "合同"@zh , "Contract"@en ;
    rdfs:comment "平等主体之间设立、变更、终止民事权利义务关系的协议"@zh .
clm:Company a owl:Class ; rdfs:label "公司"@zh , "Company"@en .
clm:Person a owl:Class ; rdfs:label "自然人"@zh , "Person"@en .
clm:Department a owl:Class ; rdfs:label "部门"@zh , "Department"@en .
clm:Project a owl:Class ; rdfs:label "项目"@zh , "Project"@en .
clm:Product a owl:Class ; rdfs:label "产品与服务"@zh , "Product"@en .
clm:Amendment a owl:Class ; rdfs:label "补充协议"@zh , "Amendment"@en ;
    rdfs:subClassOf clm:Contract .
clm:PaymentTerms a owl:Class ; rdfs:label "付款条款"@zh , "PaymentTerms"@en .
clm:Regulation a owl:Class ; rdfs:label "法规"@zh , "Regulation"@en .

clm:partyTo a owl:ObjectProperty ; rdfs:label "合同主体"@zh ;
    rdfs:domain clm:Contract ; rdfs:range clm:Company .
clm:signs a owl:ObjectProperty ; rdfs:label "签署"@zh ;
    rdfs:domain clm:Person ; rdfs:range clm:Contract .
clm:approves a owl:ObjectProperty ; rdfs:label "审批"@zh ;
    rdfs:domain clm:Person ; rdfs:range clm:Contract .
clm:involvesProduct a owl:ObjectProperty ; rdfs:label "合同标的"@zh ;
    rdfs:domain clm:Contract ; rdfs:range clm:Product .
clm:governs a owl:ObjectProperty ; rdfs:label "归口管理"@zh ;
    rdfs:domain clm:Department ; rdfs:range clm:Contract .
clm:amends a owl:ObjectProperty ; rdfs:label "修订"@zh ;
    rdfs:domain clm:Amendment ; rdfs:range clm:Contract .
clm:guarantees a owl:ObjectProperty ; rdfs:label "担保"@zh ;
    rdfs:domain clm:Company ; rdfs:range clm:Contract .

clm:amount a owl:DatatypeProperty ; rdfs:label "合同金额"@zh ;
    rdfs:domain clm:Contract ; rdfs:range xsd:decimal .
clm:currency a owl:DatatypeProperty ; rdfs:label "币种"@zh ;
    rdfs:domain clm:Contract ; rdfs:range xsd:string .
clm:signDate a owl:DatatypeProperty ; rdfs:label "签署日期"@zh ;
    rdfs:domain clm:Contract ; rdfs:range xsd:date .
clm:status a owl:DatatypeProperty ; rdfs:label "合同状态"@zh ;
    rdfs:domain clm:Contract ; rdfs:range xsd:string .
"""

# ---------------------------------------------------------------------------
# 4. 合同类别 SKOS 词表（词表浏览器）
# ---------------------------------------------------------------------------

VOCABULARY_TTL = """@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix clmv: <http://example.org/vocabulary/contract#> .

clmv:ContractTaxonomy a skos:ConceptScheme ;
    skos:prefLabel "合同分类词表"@zh , "Contract Taxonomy"@en ;
    skos:hasTopConcept clmv:Procurement , clmv:Sales , clmv:Service , clmv:Lease , clmv:Labor .

clmv:Procurement a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "采购合同"@zh ; skos:topConceptOf clmv:ContractTaxonomy ;
    skos:narrower clmv:RawMaterialProcurement , clmv:EquipmentProcurement .
clmv:RawMaterialProcurement a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "原材料采购合同"@zh ; skos:broader clmv:Procurement .
clmv:EquipmentProcurement a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "设备采购合同"@zh ; skos:broader clmv:Procurement .

clmv:Sales a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "销售合同"@zh ; skos:topConceptOf clmv:ContractTaxonomy ;
    skos:narrower clmv:ProductSales , clmv:ChannelAgency , clmv:BrandLicensing .
clmv:ProductSales a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "产品销售合同"@zh ; skos:broader clmv:Sales .
clmv:ChannelAgency a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "渠道代理合同"@zh ; skos:broader clmv:Sales .
clmv:BrandLicensing a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "品牌授权合同"@zh ; skos:broader clmv:Sales .

clmv:Service a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "服务合同"@zh ; skos:topConceptOf clmv:ContractTaxonomy ;
    skos:narrower clmv:TechnicalService , clmv:Consulting , clmv:MarketingService , clmv:Confidentiality .
clmv:TechnicalService a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "技术服务合同"@zh ; skos:broader clmv:Service ;
    skos:narrower clmv:SoftwareDevelopment , clmv:OperationMaintenance .
clmv:SoftwareDevelopment a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "软件开发合同"@zh ; skos:broader clmv:TechnicalService .
clmv:OperationMaintenance a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "运维服务合同"@zh ; skos:broader clmv:TechnicalService .
clmv:Consulting a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "咨询顾问合同"@zh ; skos:broader clmv:Service .
clmv:MarketingService a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "市场推广服务合同"@zh ; skos:broader clmv:Service .
clmv:Confidentiality a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "保密协议"@zh ; skos:broader clmv:Service .

clmv:Lease a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "租赁合同"@zh ; skos:topConceptOf clmv:ContractTaxonomy ;
    skos:narrower clmv:PropertyLease , clmv:EquipmentLease .
clmv:PropertyLease a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "房屋租赁合同"@zh ; skos:broader clmv:Lease .
clmv:EquipmentLease a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "设备租赁合同"@zh ; skos:broader clmv:Lease .

clmv:Labor a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "用工合同"@zh ; skos:topConceptOf clmv:ContractTaxonomy ;
    skos:narrower clmv:LaborDispatch .
clmv:LaborDispatch a skos:Concept ; skos:inScheme clmv:ContractTaxonomy ;
    skos:prefLabel "劳务派遣合同"@zh ; skos:broader clmv:Labor .
"""


# ---------------------------------------------------------------------------
# 5. 标注 / 推理 / 消歧 / 记忆
# ---------------------------------------------------------------------------


def post_annotations() -> None:
    annotations = [
        ("contract-05", "法务审查意见：保密期限届满后 2 年内仍不得披露技术细节，"
         "建议将保密义务扩展至关联公司。", ["法务", "保密条款"]),
        ("contract-10", "风险提示：账期条款若按乙方草案执行将占用大量营运资金，"
         "已驳回并要求改为月结 60 天。", ["财务", "付款条款"]),
        ("contract-23", "合规提示：承包方资质需在开工前完成年检复核，"
         "履约保证金条款参照 decision-03 执行。", ["合规", "工程"]),
        ("contract-25", "董事会关注：对外担保金额达净资产 32%，须提交股东会决议"
         "后方可签署（参见《公司法》第十六条）。", ["治理", "担保"]),
        ("contract-06", "用工合规：派遣用工占比已接近 10% 上限，"
         "下一年度转为服务外包以规避《劳务派遣暂行规定》风险。", ["人力资源"]),
    ]
    # 1) 写入后端标注 API（/api/annotations 记录）；幂等：该节点已有标注则跳过
    existing = _request("/api/annotations")
    annotated = {item["node_id"] for item in existing}
    for node_id, content, tags in annotations:
        if node_id in annotated:
            print(f"  标注已存在 → {node_id}（跳过）")
            continue
        _request("/api/annotations", payload={
            "node_id": node_id, "content": content, "tags": tags, "visibility": "public",
        }, method="POST")
        print(f"  标注已添加 → {node_id}")
    # 2) 同步写入节点 source/evidence 属性（检查器「来源标注」区可见）
    patch = {"nodes": [], "edges": []}
    for node_id, content, tags in annotations:
        patch["nodes"].append({
            "id": node_id, "type": "Contract",
            "properties": {
                "source": f"法务合规部{tags[0]}审查标注",
                "evidence": content,
                "provenance": "合同全生命周期审查记录",
            },
        })
    import_graph(patch)
    print("  审查意见已写入节点来源标注属性（source/evidence/provenance）")


def run_reasoning() -> None:
    """推理演练场示例：由「合同主体 + 合同标的」推断「甲乙方供应关系」。"""
    facts = [
        "party_to(company-01, contract-02)",
        "party_to(company-02, contract-02)",
        "involves_product(contract-02, product-01)",
    ]
    rules = [
        "IF party_to(?buyer, ?contract) AND party_to(?supplier, ?contract) "
        "AND involves_product(?contract, ?product) THEN supplies(?supplier, ?product)",
    ]
    result = _request("/api/reason", payload={
        "facts": facts, "rules": rules, "mode": "forward", "apply_to_graph": True,
    }, method="POST")
    inferred = result.get("inferred_facts") or result.get("inferences") or []
    print(f"  推理完成：新增推断事实 {len(inferred)} 条（已写入图谱）")


def run_dedup_check() -> None:
    result = _request("/api/enrich/dedup", payload={"threshold": 0.75}, method="POST")
    flagged = result.get("duplicates", [])
    print(f"  消歧扫描：发现 {len(flagged)} 对疑似重复实体")
    for pair in flagged[:6]:
        print(f"    - {pair.get('entity_a')} ↔ {pair.get('entity_b')} "
              f"(相似度 {pair.get('similarity', pair.get('score'))})")


def write_agent_memory() -> None:
    """生成合同审查智能体经验记忆（记忆工作区数据源）。"""
    from semantica.context.agent_memory import AgentMemory

    AGENT_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    memory = AgentMemory()
    entries = [
        ("审查金额超过 1000 万元的采购合同时，必须核对总经理办公会集体决策记录。",
         {"type": "policy", "topic": "采购审批"}),
        ("对天津渤海化工集团及其关联公司的合同，需额外核查环保合规资质与近三年行政处罚记录。",
         {"type": "experience", "topic": "供应商风险"}),
        ("付款条款超过月结 60 天的合同一律驳回重谈，参照先例 decision-02 执行。",
         {"type": "policy", "topic": "付款条款"}),
        ("《电子签名法》确认可靠电子签名与手写签名同等效力，异地签署优先走电子签通道。",
         {"type": "knowledge", "topic": "签署流程"}),
        ("对外担保超过净资产 30% 时，须先取得股东会决议，否则合同存在效力瑕疵。",
         {"type": "knowledge", "topic": "担保合规"}),
        ("与云资源类供应商签约时，务必在 SLA 中写明可用性赔付与终止条款，"
         "参考 decision-05 的终止处置经验。", {"type": "experience", "topic": "云服务"}),
        ("涉及个人信息处理的合同必须签署数据处理协议（DPA），并做个人信息保护影响评估。",
         {"type": "policy", "topic": "数据合规"}),
        ("派遣用工占比接近 10% 红线的项目，建议在合同中预留服务外包转换条款。",
         {"type": "experience", "topic": "用工合规"}),
        ("续签框架协议前，应调取上一履约周期的验收记录与付款台账作为谈判依据。",
         {"type": "experience", "topic": "续签谈判"}),
        ("美元计价合同需同步办理远期锁汇，敞口比例不超过合同金额的 80%。",
         {"type": "policy", "topic": "汇率风险管理"}),
    ]
    for content, metadata in entries:
        memory.store(content, metadata=metadata)
    memory.save(str(AGENT_MEMORY_DIR))
    print(f"  智能体记忆：写入 {len(entries)} 条经验 → {AGENT_MEMORY_DIR}")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def main() -> None:
    current = graph_node_count()
    print(f"当前图规模：{current} 个节点")

    if current == 0:
        base = build_base_dataset()
        result = import_graph(base)
        print(f"基础合同图导入：+{result['nodes_added']} 节点 / +{result['edges_added']} 边")
    else:
        print("基础合同图已存在，跳过")

    decisions = build_decision_dataset()
    result = import_graph(decisions)
    print(f"决策数据导入：+{result['nodes_added']} 决策节点 / +{result['edges_added']} 因果与关联边")

    dedup_data = build_dedup_dataset()
    result = import_graph(dedup_data)
    print(f"消歧实体导入：+{result['nodes_added']} 相似实体节点 / +{result['edges_added']} 边")

    result = _request("/api/ontology/load", payload={
        "content": ONTOLOGY_TTL, "format": "turtle",
        "name": "合同管理本体", "tags": ["contract", "clm", "demo"],
    }, method="POST")
    print(f"本体导入：{result.get('message', result.get('status', 'ok'))}")

    vocab_blob = VOCABULARY_TTL.encode("utf-8")
    result = _multipart_upload("/api/vocabulary/import", "file",
                               "contract_taxonomy.ttl", vocab_blob)
    print(f"SKOS 词表导入：{json.dumps(result, ensure_ascii=False)[:160]}")

    print("标注导入：")
    post_annotations()

    print("规则推理：")
    run_reasoning()

    print("消歧检查：")
    run_dedup_check()

    print("智能体记忆：")
    write_agent_memory()

    total = graph_node_count()
    print(f"完成：当前图共 {total} 个节点")


if __name__ == "__main__":
    main()
