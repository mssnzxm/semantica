# 启动带完整合同演示环境的 Semantica 服务
# 用法: powershell -File examples\start_contract_demo.ps1
# DeepSeek key 从本地文件 examples/deepseek_key.local.ps1 读取（已 gitignore，不会入库）

$root = Split-Path -Parent $PSScriptRoot
$env:SEMANTICA_ALLOW_ANONYMOUS = 'true'
$env:SEMANTICA_AGENT_MEMORY_PATH = Join-Path $PSScriptRoot 'agent_memory_data'

$keyFile = Join-Path $PSScriptRoot 'deepseek_key.local.ps1'
if (Test-Path $keyFile) {
    . $keyFile
} else {
    Write-Warning '未找到 examples/deepseek_key.local.ps1，跳过 DeepSeek 配置'
}

& (Join-Path $root '.venv\Scripts\python.exe') -m semantica.server
