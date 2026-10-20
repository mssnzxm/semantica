# Checklist

- [x] 仓库代码成功克隆到 `d:\work10\semantica`，目录内容完整（README.md、pyproject.toml、semantica/ 源码目录等）
- [x] 本机 Python 版本满足仓库 `pyproject.toml` 的 `requires-python` 要求（3.12.13，满足 >=3.10,<3.14）
- [x] 虚拟环境创建成功，`pip install -e .` 安装完成且无致命错误（实际用 `uv pip install -e ".[explorer]"` + faiss-cpu/fastembed）
- [x] `semantica --help` 或 `semantica --version` 命令正常输出（v0.7.0）
- [x] `semantica doctor` 健康检查通过（Python/semantica/Graph store/Vector store(faiss)/fastembed/Log dir 全部 ✓，无致命失败项）
- [x] `semantica server` 成功启动，REST API 可通过 HTTP 访问并返回响应（`/health` → 200 healthy；`POST /api/enrich/extract` → 200 实体抽取成功）
- [x] 向用户报告服务的启动状态与访问方式（地址/端口：http://127.0.0.1:8000，服务保持后台运行）
