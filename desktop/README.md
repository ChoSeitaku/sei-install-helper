# 桌面端安装说明

## 快速启动（推荐 Web 版）

```bash
# 启动服务端
cd server
pip install -r requirements.txt
python main.py

# 打开浏览器访问
http://localhost:8000/app
```

## 安装桌面端

```bash
cd desktop

# 安装依赖（可能需要几分钟）
npm install

# 启动桌面应用
npx electron .
```

## 功能特性

### 自动识别系统
- Windows: 使用 PowerShell 执行脚本
- macOS: 使用 Zsh 执行脚本  
- Linux: 使用 Bash 执行脚本

### 桌面端专属功能
- **一键运行**: 代码块按钮直接执行脚本
- **实时日志**: 执行过程实时显示
- **系统集成**: 调用系统默认浏览器打开下载链接

### 环境变量
- `ANTHROPIC_AUTH_TOKEN`: DeepSeek API Key
- `BASE_URL`: API 地址
- `AI_MODEL`: 模型名称

## 文件结构

```
desktop/
├── main.js        # Electron 主进程
├── preload.js     # 预加载脚本
└── package.json   # 依赖配置
```

## 故障排除

1. **服务端未启动**: 确保先启动 `server/main.py`
2. **Electron 安装失败**: 尝试使用淘宝镜像
   ```bash
   npm config set registry https://registry.npmmirror.com
   npm install
   ```
3. **脚本执行失败**: 检查系统是否有对应的 Shell
