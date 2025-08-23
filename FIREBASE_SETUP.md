# 🔥 Firebase 设置指南

## 📋 步骤1: 创建Firebase项目

1. 访问 [Firebase Console](https://console.firebase.google.com/)
2. 点击"创建项目"
3. 输入项目名称（例如：`hybot-stats`）
4. 选择是否启用Google Analytics（可选）
5. 点击"创建项目"

## 🔑 步骤2: 创建服务账户

1. 在Firebase控制台中，点击左侧齿轮图标 → "项目设置"
2. 切换到"服务账户"标签
3. 点击"生成新的私钥"
4. 下载JSON配置文件

## ⚙️ 步骤3: 配置环境变量

在Render中设置以下环境变量：

### 🔄 共用数据库配置（推荐）
如果您已经有Firebase数据库并想共用，只需要设置以下环境变量：

```
BOT_ID=hybot                                    # 机器人唯一标识符
FIREBASE_PROJECT_ID=your-existing-project-id    # 现有项目ID
FIREBASE_PRIVATE_KEY="your-private-key"         # 现有私钥
FIREBASE_CLIENT_EMAIL=your-service-account@...  # 现有服务账户邮箱
```

### 🆕 新建数据库配置
如果是新建Firebase项目，需要设置所有环境变量：

### 必需的环境变量：
```
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
```

### 可选的环境变量（通常使用默认值）：
```
FIREBASE_TYPE=service_account
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com
```

## 🔒 步骤4: 设置Firestore安全规则

在Firebase控制台中，转到"Firestore Database" → "规则"，设置以下规则：

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 允许所有机器人统计数据的读写
    match /bots/{botId}/stats/{document=**} {
      allow read, write: if true; // 注意：生产环境应该设置更严格的规则
    }
    
    // 兼容旧版本的数据结构（如果有的话）
    match /bot_stats/{document=**} {
      allow read, write: if true;
    }
  }
}
```

## 📊 数据结构

Firebase将自动创建以下数据结构，支持多个机器人共用：

```
bots/
├── hybot/                    # 会员机器人
│   └── stats/
│       ├── visitor_stats/
│       │   ├── total_visitors: number
│       │   ├── last_updated: timestamp
│       │   ├── bot_id: "hybot"
│       │   └── bot_name: "会员机器人"
│       └── daily_stats/
│           └── dates/
│               ├── 2025-01-20/
│               │   ├── visitors: [user_id1, user_id2, ...]
│               │   ├── total_actions: number
│               │   ├── last_updated: timestamp
│               │   └── bot_id: "hybot"
│               └── 2025-01-21/
│                   ├── visitors: [user_id3, user_id4, ...]
│                   ├── total_actions: number
│                   ├── last_updated: timestamp
│                   └── bot_id: "hybot"
├── bot2/                     # 其他机器人
│   └── stats/
│       └── ...
└── bot3/                     # 其他机器人
    └── stats/
        └── ...
```

## ✅ 验证设置

1. 部署机器人到Render
2. 发送 `/start` 命令
3. 检查Render日志，应该看到：
   - "✅ Firebase初始化成功"
   - "✅ 访客统计已同步到Firebase"

## 🚨 注意事项

1. **私钥安全**: 不要在代码中硬编码私钥
2. **环境变量**: 确保在Render中正确设置所有环境变量
3. **权限**: 服务账户需要有Firestore读写权限
4. **成本**: Firebase免费层每月有配额限制，但足够小型机器人使用

## 🔧 故障排除

### 常见错误：
- `Firebase配置不完整`: 检查环境变量是否设置正确
- `Firebase初始化失败`: 检查私钥格式和项目ID
- `权限被拒绝`: 检查Firestore安全规则

### 调试技巧：
- 查看Render日志中的详细错误信息
- 使用Firebase控制台检查数据是否正确写入
- 验证服务账户权限设置
