"""装了吗 - FastAPI 服务端"""
import os
import json
import sqlite3
import re
import hashlib
from typing import Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_PATH = os.path.join(os.path.dirname(__file__), "zhuangle.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS software (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        display_name TEXT,
        description TEXT,
        category TEXT,
        source_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        software_id INTEGER NOT NULL,
        version TEXT NOT NULL,
        platform TEXT DEFAULT 'all',
        is_stable BOOLEAN DEFAULT 1,
        FOREIGN KEY (software_id) REFERENCES software(id),
        UNIQUE(software_id, version, platform)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS install_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        software_id INTEGER NOT NULL,
        platform TEXT NOT NULL,
        plan_content TEXT NOT NULL,
        script_powershell TEXT,
        script_bash TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (software_id) REFERENCES software(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        software_id INTEGER,
        plan_id INTEGER,
        is_valid BOOLEAN NOT NULL,
        comment TEXT,
        platform TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        software_id INTEGER,
        platform TEXT,
        action TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

def seed_preset_software():
    presets = [
        # 运行时
        ("node", "Node.js", "JavaScript 运行时", "runtime", "npm"),
        ("python", "Python", "Python 编程语言", "runtime", "pypi"),
        ("java", "Java JDK", "Java 开发工具包", "runtime", "official"),
        ("golang", "Go", "Go 编程语言", "runtime", "official"),
        ("rust", "Rust", "Rust 编程语言", "runtime", "rustup"),
        ("dotnet", ".NET SDK", "微软开发框架", "runtime", "official"),
        ("php", "PHP", "PHP 脚本语言", "runtime", "official"),
        ("ruby", "Ruby", "Ruby 编程语言", "runtime", "official"),
        ("swift", "Swift", "Apple 编程语言", "runtime", "official"),
        ("kotlin", "Kotlin", "Kotlin 编程语言", "runtime", "official"),
        ("dart", "Dart", "Dart 编程语言", "runtime", "official"),
        ("r", "R", "统计分析语言", "runtime", "official"),
        ("julia", "Julia", "科学计算语言", "runtime", "official"),
        # 编辑器 & IDE
        ("vscode", "Visual Studio Code", "代码编辑器", "editor", "official"),
        ("vim", "Vim", "文本编辑器", "editor", "official"),
        ("neovim", "Neovim", "现代化 Vim 编辑器", "editor", "official"),
        ("sublime", "Sublime Text", "轻量级代码编辑器", "editor", "official"),
        ("notepad++", "Notepad++", "Windows 文本编辑器", "editor", "official"),
        ("idea", "IntelliJ IDEA", "Java IDE", "editor", "official"),
        ("pycharm", "PyCharm", "Python IDE", "editor", "official"),
        ("webstorm", "WebStorm", "JavaScript IDE", "editor", "official"),
        ("android-studio", "Android Studio", "Android 开发 IDE", "editor", "official"),
        ("xcode", "Xcode", "macOS/iOS 开发 IDE", "editor", "official"),
        ("cursor", "Cursor", "AI 代码编辑器", "editor", "official"),
        # 工具
        ("git", "Git", "版本控制系统", "tools", "official"),
        ("curl", "cURL", "命令行数据传输工具", "tools", "official"),
        ("wget", "Wget", "网络下载工具", "tools", "official"),
        ("jq", "jq", "命令行 JSON 处理器", "tools", "official"),
        ("tree", "Tree", "目录结构显示工具", "tools", "official"),
        ("htop", "htop", "交互式进程查看器", "tools", "official"),
        ("bat", "bat", "带语法高亮的 cat 替代", "tools", "github"),
        ("fzf", "fzf", "命令行模糊查找器", "tools", "github"),
        ("ripgrep", "ripgrep", "高速搜索工具", "tools", "github"),
        ("fd", "fd", "快速查找工具", "tools", "github"),
        ("exa", "exa", "现代化 ls 替代", "tools", "github"),
        ("zoxide", "zoxide", "智能 cd 命令", "tools", "github"),
        ("starship", "Starship", "跨平台 Shell 提示符", "tools", "github"),
        # 浏览器
        ("chrome", "Google Chrome", "网页浏览器", "browser", "official"),
        ("firefox", "Firefox", "开源网页浏览器", "browser", "official"),
        ("edge", "Microsoft Edge", "微软浏览器", "browser", "official"),
        ("brave", "Brave", "隐私浏览器", "browser", "official"),
        ("opera", "Opera", "浏览器", "browser", "official"),
        # 数据库
        ("redis", "Redis", "内存数据库", "database", "official"),
        ("postgresql", "PostgreSQL", "关系型数据库", "database", "official"),
        ("mysql", "MySQL", "关系型数据库", "database", "official"),
        ("mongodb", "MongoDB", "文档数据库", "database", "official"),
        ("sqlite", "SQLite", "嵌入式数据库", "database", "official"),
        ("mariadb", "MariaDB", "MySQL 分支", "database", "official"),
        ("elasticsearch", "Elasticsearch", "搜索引擎", "database", "official"),
        ("influxdb", "InfluxDB", "时序数据库", "database", "official"),
        # 服务器 & 中间件
        ("nginx", "Nginx", "Web 服务器", "server", "official"),
        ("apache", "Apache", "Web 服务器", "server", "official"),
        ("caddy", "Caddy", "自动 HTTPS 服务器", "server", "github"),
        ("traefik", "Traefik", "云原生代理", "server", "github"),
        ("rabbitmq", "RabbitMQ", "消息队列", "server", "official"),
        ("kafka", "Apache Kafka", "流处理平台", "server", "official"),
        ("tomcat", "Apache Tomcat", "Java Servlet 容器", "server", "official"),
        # DevOps & 容器
        ("docker", "Docker", "容器化平台", "devops", "official"),
        ("kubectl", "kubectl", "Kubernetes 命令行工具", "devops", "official"),
        ("terraform", "Terraform", "基础设施即代码工具", "devops", "official"),
        ("ansible", "Ansible", "自动化运维工具", "devops", "official"),
        ("vagrant", "Vagrant", "虚拟环境管理", "devops", "official"),
        ("puppeteer", "Puppeteer", "浏览器自动化", "devops", "npm"),
        ("helm", "Helm", "Kubernetes 包管理器", "devops", "official"),
        ("istioctl", "Istioctl", "Istio 命令行工具", "devops", "official"),
        # 云工具
        ("aws", "AWS CLI", "AWS 命令行工具", "cloud", "official"),
        ("azure", "Azure CLI", "Azure 命令行工具", "cloud", "official"),
        ("gcloud", "Google Cloud CLI", "Google Cloud 命令行工具", "cloud", "official"),
        ("firebase", "Firebase CLI", "Firebase 命令行工具", "cloud", "npm"),
        ("vercel", "Vercel CLI", "Vercel 部署工具", "cloud", "npm"),
        ("netlify", "Netlify CLI", "Netlify 部署工具", "cloud", "npm"),
        ("heroku", "Heroku CLI", "Heroku 命令行工具", "cloud", "official"),
        # 包管理器
        ("npm", "npm", "Node.js 包管理器", "package", "npm"),
        ("yarn", "Yarn", "JavaScript 包管理器", "package", "npm"),
        ("pnpm", "pnpm", "高效 Node.js 包管理器", "package", "npm"),
        ("bun", "Bun", "JavaScript 运行时和包管理器", "package", "official"),
        ("pip", "pip", "Python 包管理器", "package", "pypi"),
        ("conda", "Conda", "Python 环境管理器", "package", "official"),
        ("poetry", "Poetry", "Python 依赖管理工具", "package", "pypi"),
        ("cargo", "Cargo", "Rust 包管理器", "package", "rustup"),
        ("brew", "Homebrew", "macOS 包管理器", "package", "official"),
        ("scoop", "Scoop", "Windows 命令行安装器", "package", "official"),
        ("choco", "Chocolatey", "Windows 包管理器", "package", "official"),
        ("winget", "winget", "Windows 包管理器", "package", "official"),
        ("apt", "apt", "Debian/Ubuntu 包管理器", "package", "official"),
        ("yum", "yum", "CentOS/RHEL 包管理器", "package", "official"),
        # 构建工具
        ("cmake", "CMake", "跨平台编译工具", "build", "official"),
        ("gradle", "Gradle", "构建自动化工具", "build", "official"),
        ("maven", "Maven", "Java 项目管理工具", "build", "maven"),
        ("make", "Make", "构建工具", "build", "official"),
        ("webpack", "Webpack", "JavaScript 模块打包器", "build", "npm"),
        ("vite", "Vite", "前端构建工具", "build", "npm"),
        ("esbuild", "esbuild", "极速 JavaScript 打包器", "build", "npm"),
        ("rollup", "Rollup", "JavaScript 模块打包器", "build", "npm"),
        ("turbo", "Turborepo", "monorepo 构建系统", "build", "npm"),
        # 多媒体
        ("ffmpeg", "FFmpeg", "音视频处理工具", "multimedia", "official"),
        ("imagemagick", "ImageMagick", "图像处理工具", "multimedia", "official"),
        ("obsidian", "Obsidian", "知识管理工具", "multimedia", "official"),
        ("vlc", "VLC", "多媒体播放器", "multimedia", "official"),
        ("gimp", "GIMP", "图像编辑器", "multimedia", "official"),
        ("blender", "Blender", "3D 建模软件", "multimedia", "official"),
        # AI & 机器学习
        ("ollama", "Ollama", "本地大模型运行工具", "ai", "official"),
        ("jupyter", "Jupyter Notebook", "交互式计算环境", "ai", "pypi"),
        ("tensorboard", "TensorBoard", "机器学习可视化", "ai", "pypi"),
        ("wandb", "Weights & Biases", "机器学习实验跟踪", "ai", "pypi"),
        # 安全工具
        ("nmap", "Nmap", "网络扫描工具", "security", "official"),
        ("openssl", "OpenSSL", "加密工具", "security", "official"),
        ("wireguard", "WireGuard", "VPN 工具", "security", "official"),
        # 办公 & 效率
        ("obsidian", "Obsidian", "知识管理工具", "productivity", "official"),
        ("notion", "Notion", "协作与笔记工具", "productivity", "official"),
        ("slack", "Slack", "团队协作工具", "productivity", "official"),
        ("discord", "Discord", "语音聊天工具", "productivity", "official"),
        ("zoom", "Zoom", "视频会议工具", "productivity", "official"),
        # 其他开发工具
        ("postman", "Postman", "API 测试工具", "tools", "official"),
        ("insomnia", "Insomnia", "API 客户端", "tools", "official"),
        ("dbeaver", "DBeaver", "通用数据库工具", "tools", "official"),
        ("pgadmin", "pgAdmin", "PostgreSQL 管理工具", "tools", "official"),
        ("redis-desktop", "Redis Desktop Manager", "Redis 可视化工具", "tools", "official"),
        ("httpie", "HTTPie", "现代 HTTP 客户端", "tools", "official"),
        ("mockoon", "Mockoon", "API 模拟工具", "tools", "official"),
    ]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for p in presets:
        try:
            c.execute("INSERT OR IGNORE INTO software (name, display_name, description, category, source_type) VALUES (?,?,?,?,?)", p)
        except:
            pass
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_preset_software()
    yield

app = FastAPI(title="装了吗 API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_ai_config():
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    base_url = os.environ.get("BASE_URL", "https://api.openai.com/v1")
    config_path = os.path.expanduser("~/.claude/settings.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                s = json.load(f)
                if "ANTHROPIC_AUTH_TOKEN" in s:
                    api_key = s["ANTHROPIC_AUTH_TOKEN"]
                if "BASE_URL" in s:
                    base_url = s["BASE_URL"]
        except:
            pass
    return {"api_key": api_key, "base_url": base_url, "model": os.environ.get("AI_MODEL", "gpt-4")}

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

class SearchRequest(BaseModel):
    query: str
    platform: str = "windows"

class PlanRequest(BaseModel):
    software_id: int
    version: Optional[str] = None
    platform: str = "windows"

class FeedbackRequest(BaseModel):
    software_id: int
    plan_id: int
    is_valid: bool
    comment: Optional[str] = None
    platform: str = "windows"

@app.get("/")
async def root():
    return {"message": "装了吗 API", "version": "1.0.0"}

@app.get("/api")
async def api_root():
    return {
        "message": "装了吗 API",
        "version": "1.0.0",
        "endpoints": {
            "search": "POST /api/search",
            "software": "GET /api/software",
            "versions": "GET /api/software/{id}/versions",
            "generate": "POST /api/plans/generate",
            "feedback": "POST /api/feedback",
            "stats": "GET /api/stats",
            "app": "GET /app"
        }
    }

@app.get("/app", response_class=HTMLResponse)
async def serve_app():
    index_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            return f.read()
    return "<h1>Frontend not found</h1>"

@app.post("/api/search")
async def search(request: SearchRequest, db=Depends(get_db)):
    c = db.cursor()
    q = f"%{request.query}%"
    c.execute("SELECT * FROM software WHERE name LIKE ? OR display_name LIKE ? OR description LIKE ? ORDER BY name LIMIT 20", (q, q, q))
    return {"results": [dict(r) for r in c.fetchall()]}

@app.get("/api/software")
async def list_software(limit: int = 50, db=Depends(get_db)):
    c = db.cursor()
    c.execute("SELECT * FROM software ORDER BY name LIMIT ?", (limit,))
    return {"results": [dict(r) for r in c.fetchall()]}

@app.get("/api/software/{sid}/versions")
async def get_versions(sid: int, db=Depends(get_db)):
    c = db.cursor()
    c.execute("SELECT * FROM versions WHERE software_id=? ORDER BY is_stable DESC, version DESC", (sid,))
    results = [dict(r) for r in c.fetchall()]
    
    # If no versions cached, fetch from source
    if not results:
        return await fetch_versions(sid, db)
    
    return {"results": results}

@app.post("/api/software/{sid}/versions/fetch")
async def fetch_versions(sid: int, db=Depends(get_db)):
    c = db.cursor()
    c.execute("SELECT * FROM software WHERE id=?", (sid,))
    sw = c.fetchone()
    if not sw:
        raise HTTPException(404, "Software not found")
    sw = dict(sw)
    
    versions = []
    
    async with httpx.AsyncClient() as client:
        try:
            if sw["source_type"] == "npm":
                resp = await client.get(f"https://registry.npmjs.org/{sw['name']}", timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    dist_tags = data.get("dist-tags", {})
                    if "latest" in dist_tags:
                        versions.append({"version": dist_tags["latest"], "is_stable": True})
                    if "lts" in dist_tags:
                        versions.append({"version": f"LTS ({dist_tags['lts']})", "is_stable": True})
                    all_versions = list(data.get("versions", {}).keys())
                    for v in all_versions[-8:]:
                        if v not in [x["version"] for x in versions]:
                            versions.append({"version": v, "is_stable": False})
                            
            elif sw["source_type"] == "pypi":
                resp = await client.get(f"https://pypi.org/pypi/{sw['name']}/json", timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    versions.append({"version": data["info"]["version"], "is_stable": True})
                    for v in list(data.get("releases", {}).keys())[-8:]:
                        if v not in [x["version"] for x in versions]:
                            versions.append({"version": v, "is_stable": False})
                            
            elif sw["source_type"] == "github":
                resp = await client.get(
                    f"https://api.github.com/repos/{sw['name']}/releases?per_page=10",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=15
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for r in data[:8]:
                        tag = r.get("tag_name", "").lstrip("v")
                        if tag and tag not in [x["version"] for x in versions]:
                            versions.append({"version": tag, "is_stable": not r.get("prerelease", False)})
                            
            elif sw["source_type"] == "rustup":
                versions = [
                    {"version": "stable", "is_stable": True},
                    {"version": "beta", "is_stable": False},
                    {"version": "nightly", "is_stable": False}
                ]
                
            elif sw["source_type"] == "official":
                # Provide common versions for well-known software
                common_versions = {
                    "mysql": ["8.4.0", "8.3.0", "8.2.0", "8.1.0", "8.0.36", "5.7.44"],
                    "postgresql": ["16.2", "15.6", "14.11", "13.14", "12.18"],
                    "redis": ["7.2.4", "7.0.15", "6.2.14"],
                    "nginx": ["1.25.4", "1.24.0", "1.22.1"],
                    "mongodb": ["7.0.5", "6.0.13", "5.0.24"],
                    "docker": ["25.0.3", "24.0.8", "23.0.7"],
                    "git": ["2.43.0", "2.42.0", "2.41.0"],
                    "java": ["21.0.2", "17.0.10", "11.0.22", "8.0.401"],
                    "golang": ["1.22.0", "1.21.7", "1.20.14"],
                    "node": ["20.11.0", "18.19.0"],
                    "python": ["3.12.2", "3.11.8", "3.10.13", "3.9.18"],
                    "ruby": ["3.3.0", "3.2.3", "3.1.4"],
                    "php": ["8.3.3", "8.2.15", "8.1.27"],
                    "dotnet": ["8.0.2", "7.0.16", "6.0.27"],
                    "ffmpeg": ["6.1.1", "5.1.5", "4.4.4"],
                    "nginx": ["1.25.4", "1.24.0"],
                    "apache": ["2.4.58", "2.4.57"],
                    "tomcat": ["10.1.18", "9.0.85", "8.5.99"],
                    "elastic": ["8.12.2", "7.17.18"],
                    "mongo": ["7.0.5", "6.0.13"],
                    "rabbitmq": ["3.13.0", "3.12.13"],
                    "kafka": ["3.7.0", "3.6.1"],
                }
                name_lower = sw["name"].lower()
                for key, vers in common_versions.items():
                    if key in name_lower:
                        for v in vers:
                            versions.append({"version": v, "is_stable": True})
                        break
                if not versions:
                    versions = [
                        {"version": "latest", "is_stable": True},
                        {"version": "stable", "is_stable": True}
                    ]
                
        except Exception as e:
            print(f"Fetch versions error: {e}")
    
    # Provide defaults if no versions found
    if not versions:
        versions = [
            {"version": "latest", "is_stable": True},
            {"version": "stable", "is_stable": True}
        ]
    
    # Save to database
    for v in versions[:10]:
        try:
            c.execute("INSERT OR IGNORE INTO versions (software_id, version, platform, is_stable) VALUES (?, ?, 'all', ?)",
                      (sid, v["version"], v.get("is_stable", True)))
        except:
            pass
    db.commit()
    
    c.execute("SELECT * FROM versions WHERE software_id=? ORDER BY is_stable DESC, version DESC", (sid,))
    return {"results": [dict(r) for r in c.fetchall()]}

def make_default_plan(sw, version):
    name = sw['name']
    display = sw['display_name']
    
    # Software-specific detection commands
    detect_commands = {
        "node": ("node --version", "Node.js"),
        "python": ("python --version", "Python"),
        "git": ("git --version", "Git"),
        "docker": ("docker --version", "Docker"),
        "java": ("java -version", "Java"),
        "golang": ("go version", "Go"),
        "rust": ("rustc --version", "Rust"),
        "ruby": ("ruby --version", "Ruby"),
        "php": ("php --version", "PHP"),
        "mysql": ("mysql --version", "MySQL"),
        "postgresql": ("psql --version", "PostgreSQL"),
        "redis": ("redis-server --version", "Redis"),
        "nginx": ("nginx -v", "Nginx"),
        "curl": ("curl --version", "cURL"),
        "wget": ("wget --version", "Wget"),
        "vim": ("vim --version", "Vim"),
        "ffmpeg": ("ffmpeg -version", "FFmpeg"),
        "dotnet": ("dotnet --version", ".NET"),
        "cmake": ("cmake --version", "CMake"),
        "gradle": ("gradle --version", "Gradle"),
        "maven": ("mvn --version", "Maven"),
    }
    
    detect_cmd, detect_name = detect_commands.get(name, (f"{name} --version", display))
    
    return f"""# {display} 安装方案

## 环境检测

安装前先检测是否已安装：

```powershell
# 检测 {detect_name} 是否已安装
{detect_cmd} 2>$null
if ($LASTEXITCODE -eq 0) {{
    Write-Host "[OK] {detect_name} 已安装" -ForegroundColor Green
    Write-Host "跳过安装，直接使用"
    exit 0
}} else {{
    Write-Host "[INFO] {detect_name} 未检测到，开始安装..." -ForegroundColor Yellow
}}
```

```bash
# 检测 {detect_name} 是否已安装
if command -v {name} &> /dev/null; then
    echo "[OK] {detect_name} 已安装"
    {detect_cmd}
    echo "跳过安装，直接使用"
    exit 0
else
    echo "[INFO] {detect_name} 未检测到，开始安装..."
fi
```

## 下载链接

- **官方下载**: 请访问官网下载最新版本

## 安装步骤

```powershell
# {display} 安装脚本
# 请以管理员权限运行

# 1. 检测是否已安装
{detect_cmd} 2>$null
if ($LASTEXITCODE -eq 0) {{
    Write-Host "[OK] {detect_name} 已安装，版本:" -ForegroundColor Green
    {detect_cmd}
    exit 0
}}

# 2. 下载安装包（示例）
Write-Host "请从官网下载 {display} 安装包" -ForegroundColor Cyan
Write-Host "下载地址: https://www.{name}.org/downloads"

# 3. 安装完成后验证
Write-Host "`n安装完成后，请重新打开终端验证：" -ForegroundColor Yellow
Write-Host "{detect_cmd}"
```

```bash
# {display} 安装脚本

# 1. 检测是否已安装
if command -v {name} &> /dev/null; then
    echo "[OK] {detect_name} 已安装"
    {detect_cmd}
    exit 0
fi

# 2. 安装（以 Ubuntu 为例）
echo "请根据系统选择安装命令："
echo "  Ubuntu/Debian: sudo apt install {name}"
echo "  CentOS/RHEL: sudo yum install {name}"
echo "  macOS: brew install {name}"

# 3. 安装完成后验证
echo "安装完成后运行: {detect_cmd}"
```

## 验证安装

```powershell
# 验证 {detect_name} 安装
{detect_cmd}
Write-Host "`n{detect_name} 安装成功！" -ForegroundColor Green
```

```bash
# 验证 {detect_name} 安装
{detect_cmd}
echo "{detect_name} 安装成功！"
```

---
*提示：如果已安装会自动跳过，不会重复安装*"""

def extract_scripts(plan_content):
    ps = re.search(r'```powershell\s*\n(.*?)```', plan_content, re.DOTALL)
    bs = re.search(r'```bash\s*\n(.*?)```', plan_content, re.DOTALL)
    return (ps.group(1).strip() if ps else ""), (bs.group(1).strip() if bs else "")

@app.post("/api/plans/generate")
async def generate_plan(req: PlanRequest, db=Depends(get_db)):
    c = db.cursor()
    c.execute("SELECT * FROM software WHERE id=?", (req.software_id,))
    sw = c.fetchone()
    if not sw:
        raise HTTPException(404, "Software not found")
    sw = dict(sw)
    
    version = req.version or "latest"
    
    c.execute("SELECT plan_content FROM install_plans WHERE software_id=? AND platform=? LIMIT 1", 
              (req.software_id, req.platform))
    cached = c.fetchone()
    
    if cached:
        plan_content = cached[0]
        plan_id = None
    else:
        plan_content = None
        ai = get_ai_config()
        prompt = f"""为 {sw['display_name']} (版本: {version}) 生成安装方案。
平台: {req.platform}

必须包含以下内容：
1. 环境检测：先检测是否已安装，如果已安装则跳过（用 version 命令检测）
2. 中文注释说明每一步
3. 下载链接（如有官方安装包）
4. 安装步骤
5. 环境变量配置（如需要）
6. 验证安装命令
7. 常见问题处理

格式要求：
- 用 Markdown 格式
- 包含 ```powershell 和 ```bash 代码块
- PowerShell 脚本开头先检测：if ((Get-Command xxx -ErrorAction SilentlyContinue)) {{ Write-Host "已安装"; exit 0 }}
- Bash 脚本开头先检测：if command -v xxx &> /dev/null; then echo "已安装"; exit 0; fi
- 不要推荐学习资源"""
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{ai['base_url']}/chat/completions",
                    headers={"Authorization": f"Bearer {ai['api_key']}", "Content-Type": "application/json"},
                    json={"model": ai["model"], "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
                    timeout=60
                )
                if resp.status_code == 200:
                    plan_content = resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"AI error: {e}")
        
        if not plan_content:
            plan_content = make_default_plan(sw, version)
        
        script_ps, script_bash = extract_scripts(plan_content)
        c.execute("INSERT INTO install_plans (software_id, platform, plan_content, script_powershell, script_bash) VALUES (?,?,?,?,?)",
                  (req.software_id, req.platform, plan_content, script_ps, script_bash))
        db.commit()
        plan_id = c.lastrowid
    
    c.execute("INSERT INTO stats (software_id, platform, action) VALUES (?,?,?)", 
              (req.software_id, req.platform, "generate"))
    db.commit()
    
    script_ps, script_bash = extract_scripts(plan_content)
    
    return {
        "plan_id": plan_id,
        "plan_content": plan_content,
        "script_powershell": script_ps,
        "script_bash": script_bash
    }

@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest, db=Depends(get_db)):
    c = db.cursor()
    c.execute("INSERT INTO feedback (software_id, plan_id, is_valid, comment, platform) VALUES (?,?,?,?,?)",
              (req.software_id, req.plan_id, req.is_valid, req.comment, req.platform))
    db.commit()
    return {"message": "OK"}

@app.get("/api/stats")
async def get_stats(db=Depends(get_db)):
    c = db.cursor()
    c.execute("SELECT s.display_name, COUNT(*) FROM stats st JOIN software s ON st.software_id=s.id GROUP BY s.id ORDER BY COUNT(*) DESC LIMIT 10")
    soft = [{"name": r[0], "count": r[1]} for r in c.fetchall()]
    c.execute("SELECT platform, COUNT(*) FROM stats GROUP BY platform ORDER BY COUNT(*) DESC")
    plat = [{"platform": r[0], "count": r[1]} for r in c.fetchall()]
    c.execute("SELECT SUM(CASE WHEN is_valid=1 THEN 1 ELSE 0 END), SUM(CASE WHEN is_valid=0 THEN 1 ELSE 0 END) FROM feedback")
    fb = c.fetchone()
    return {"software_stats": soft, "platform_stats": plat, "feedback_stats": {"valid": fb[0] or 0, "invalid": fb[1] or 0}}

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "zhuangle2024")

class LoginRequest(BaseModel):
    password: str

@app.post("/api/admin/login")
async def admin_login(req: LoginRequest):
    if req.password == ADMIN_PASSWORD:
        return {"token": hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()}
    raise HTTPException(401, "Wrong password")

@app.get("/api/admin/plans")
async def admin_plans(limit: int = 50, db=Depends(get_db)):
    c = db.cursor()
    c.execute("""SELECT p.*, s.display_name, s.name as software_name 
        FROM install_plans p JOIN software s ON p.software_id=s.id 
        ORDER BY p.updated_at DESC LIMIT ?""", (limit,))
    return {"results": [dict(r) for r in c.fetchall()]}

@app.delete("/api/admin/plans/{pid}")
async def admin_delete_plan(pid: int, db=Depends(get_db)):
    db.execute("DELETE FROM install_plans WHERE id=?", (pid,))
    db.commit()
    return {"message": "Deleted"}

@app.get("/api/admin/feedback")
async def admin_feedback(limit: int = 50, db=Depends(get_db)):
    c = db.cursor()
    c.execute("""SELECT f.*, s.display_name, s.name as software_name 
        FROM feedback f LEFT JOIN software s ON f.software_id=s.id 
        ORDER BY f.created_at DESC LIMIT ?""", (limit,))
    return {"results": [dict(r) for r in c.fetchall()]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
