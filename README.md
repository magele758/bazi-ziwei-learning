# 八字与紫微斗数：两个独立推算应用

本仓库包含两个**原理不同、数据模型不同**的 Web 小项目，分别用于**界面化推算**。二者常被并列讨论，但**不是同一套算法的两种界面**，不宜混为一谈。

## 一句话区分

| 维度 | 八字（四柱） | 紫微斗数 |
|------|----------------|-----------|
| **核心对象** | 出生时刻在历法上的**干支编码**（四柱八字） | 以**命盘十二宫**为坐标系，**星曜**落入各宫 |
| **时间粒度** | 以**节气**定月柱、以**时辰**定柱；强调**五行生克、十神、格局、运岁** | 以农历（或定盘规则）**安星**；强调**宫位关系、星曜庙旺、四化、大限流年** |
| **输出形态** | 四柱干支 + 五行/十神等衍生 | 十二宫盘 + 星曜分布 +（可扩展）大限流年 |
| **典型用途** | 论命以**干支组合与运程**为主线 | 论命以**宫位人事与星曜组合**为主线 |

## 学理层面的差异（便于选型）

1. **建模方式**  
   - **八字**：把出生时间压缩成 8 个字（四柱），再用干支系统做生克制化、扶抑、从格等分析。  
   - **紫微**：把人生领域拆成**十二宫**（命、兄、夫、子等），看**哪些星**落在哪些宫、宫与宫之间如何呼应。

2. **“月份”概念**  
   - **八字月柱**通常与**节气月**绑定（非农历初一换月）。  
   - **紫微排盘**传统上多依**农历月、时**安星（具体流派有细差，本项目在子目录 README 中写明采用的规则）。

3. **可解释性与争议点**  
   - 二者都有流派与口径差异（例如真太阳时、早晚子时、紫微派别）。Web 演示重在**口径自洽 + 可复现**；重要决策勿以单一排盘为准。

## 目录结构

```
八字和紫薇/
├── README.md          # 本文件：二者区分与总览
├── common/            # 共用模块（如 AI 解读，OpenAI 兼容 API）
├── bazi-web/          # 四柱八字 Web（原理见该目录 README）
└── ziwei-web/         # 紫微斗数 Web（原理见该目录 README）
```

## 环境（Python / conda）

两个子项目均为 Flask 应用。**紫微全量盘**依赖 **py-iztro**（内含 **pythonmonkey** 加载 JS），对运行环境要求略高于纯 Python；若安装失败请查看 [py-iztro 说明](https://github.com/x-haose/py-iztro)。

```bash
conda create -n mingli-web python=3.11 -y
conda activate mingli-web
pip install -r requirements.txt
```

自检（不启动服务）：

```bash
pytest
```

生产或对外监听时建议关闭 Flask 调试页：`export FLASK_DEBUG=false`。

**安全相关环境变量（对外部署时请设置）：**

| 变量 | 说明 |
|------|------|
| `FLASK_SECRET_KEY` | 用于 CSRF 与会话签名，**勿用默认值**；可 `python -c "import secrets; print(secrets.token_hex(32))"` |
| `MAX_CONTENT_LENGTH` | 请求体上限（字节），默认 `524288`（512KB） |
| `FLASK_DISABLE_CSRF` | 设为 `1` 可关闭 CSRF 校验（仅调试，**勿用于公网**） |
| `FLASK_DISABLE_RATELIMIT` | 设为 `1` 关闭 POST 限流（默认每 IP 每分钟 120 次 POST） |
| `RATELIMIT_STORAGE_URI` | 多进程限流可改为 Redis，如 `redis://localhost:6379` |

对外请放在 **HTTPS反向代理**（nginx、Caddy 等）后面，由代理终结 TLS。

### 生产进程示例（gunicorn）

在仓库根目录已安装依赖的前提下（`pip install -r requirements.txt`）：

```bash
export FLASK_DEBUG=false
export FLASK_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"

# 八字（`--factory` 调用 `create_app`）
cd bazi-web && gunicorn --factory -w 1 -b 127.0.0.1:5001 'app:create_app'

# 紫微（建议 workers=1，与 pythonmonkey 兼容性更稳）
cd ziwei-web && gunicorn --factory -w 1 -b 127.0.0.1:5002 'app:create_app'
```

### 运行

```bash
conda activate mingli-web

# 八字
cd bazi-web && python app.py
# 浏览器打开 http://127.0.0.1:5001

# 紫微（另开终端）
cd ziwei-web && python app.py
# 浏览器打开 http://127.0.0.1:5002
```

**若紫微一点查询终端/浏览器就闪退：**不要用带**热重载**的方式启动（例如 `flask run` 默认会启两个进程）。请用上面的 `python app.py`（已关闭 `use_reloader`），或 `flask run --no-reload`。

## AI 解读报告（可选）

排盘成功后页面有「生成 AI 解读」按钮。服务端将**当前排盘摘要**发往 **OpenAI 兼容**的 Chat Completions 接口（默认 `https://api.openai.com/v1`），**API Key 只读环境变量**，不会出现在浏览器。

```bash
export OPENAI_API_KEY="sk-..."
# 可选：自建或第三方兼容网关
# export OPENAI_BASE_URL="https://api.example.com/v1"
# export OPENAI_MODEL="gpt-4o-mini"
```

依赖：`httpx`（已写入各子目录 `requirements.txt`）。请注意：**生辰与性别会随请求发送到模型服务商**，若介意隐私请使用本地模型或不要点击该按钮。

## 免责声明

本项目用于**文化学习与算法演示**，不构成任何决策建议。命理内容无科学依据，请理性对待。
