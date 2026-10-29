# 脚本参考文档

## extract_noise.py

从 `Pods/` 目录扫描真正的开源第三方库源码，提取标识符生成 `noise_strings.json` 降噪库。
**注意：必须使用 `--include` 明确指定真正第三方的开源组件，绝不能把公司的私有/业务组件提取为噪声！**

```bash
# 执行提取，仅提取已鉴别的开源库
python3 scripts/extract_noise.py \
  --pods-dir famo-ios/Pods \
  --include AFNetworking,SDWebImage,Masonry,MJExtension \
  --output noise/noise_strings.json
```

## extract.py

从 `.ipa` 文件或 `.app` 目录提取全量指纹。

```bash
# 从 .ipa 文件提取
python3 scripts/extract.py --input Famo.ipa --output fingerprints/famo_v2.14.json

# 从已解压的 .app 目录提取
python3 scripts/extract.py --input Famo.app --output fingerprints/famo_v2.14.json
```

### 检测维度

**🔴 高优先级 — 二进制**

| 维度 | 当前已实现 | 规划中能力 |
|------|------------|------------|
| 主二进制字符串 | `strings -n 6`，URL 与无空格长字符串（>30）单独归类 | 增加 `otool -s __TEXT __cstring` 直读与更细粒度分类 |
| 主二进制符号表 | `nm -gU`，过滤常见系统前缀 | 增加协议/接口符号专项分层 |
| 链接 Framework 列表 | `otool -L` 输出 `.framework` / `.dylib` | 增加 framework 版本与签名特征 |
| 私有 Framework 二进制 | 遍历 `Frameworks/*.framework` 并复用字符串+符号分析 | 增加 framework 级调用图与类型特征 |
| App Extension 二进制 | 遍历 `*.appex` 并复用字符串+符号分析 | 增加 extension 间依赖关系比对 |
| Swift 类型元数据 | 基于 `nm -gU` + `swift-demangle` 归纳类型名 | 接入 `__swift5_types` 原始段解析提升精度 |
| 函数调用图哈希 | 基于 `otool -tV` 指令流转移关系生成稳定哈希 | 增加更完整 CFG 语义建模 |

**🔴 高优先级 — 资源与元数据**

| 维度 | 当前已实现 | 规划中能力 |
|------|------------|------------|
| Assets.car 资产名列表 | `assetutil -I` 提取名称 | 增加资源层级与变体信息 |
| Assets.car 图片感知哈希 | 依赖 `cartool` 可选产出 `assets_car_images` | 内置 Assets.car 图像提取，去除外部依赖 |
| App 图标感知哈希 | dHash，可识别改色调/缩放 | 增加多尺寸图标聚合策略 |
| 第三方 SDK 凭证 | plist 解析，覆盖 Facebook/Firebase/Google 常见字段 | 扩展 Agora/Adjust 等更多 SDK 键位 |
| Info.plist 权限文案 | 提取 `NS*UsageDescription` + URL Scheme | 增加权限文案语义归一化标签 |
| Entitlements | `codesign -d --entitlements` 提取 app group/keychain/team id | 增加 entitlement 差异级别分类 |
| 本地化文案 | 解析 `.lproj/Localizable.strings` key-value | 扩展更多 `.strings` 文件与格式容错 |
| Privacy 清单 | 扫描 `PrivacyInfo.xcprivacy` 并结构化输出 `manifests` | 增加多层级归并与风险标签 |
| 配置文件 | 扫描 JSON/plist/yaml/ini/conf/properties/env/data 并提取 keys/样本串 | 增加更强的密钥与端点识别策略 |

**🟡 中优先级**

| 维度 | 当前已实现 | 规划中能力 |
|------|------------|------------|
| Lottie 动画文件 | 文件名包含 `lottie` 的 `.json`，输出 MD5 | 增加内容结构指纹而非仅文件哈希 |
| 音频文件 | `.mp3/.wav/.m4a/.caf` 输出 MD5 | 增加音频时长/声纹特征 |
| 自定义字体 | `.ttf/.otf` 输出 MD5 | 增加字体族与字形覆盖度特征 |
| 散落资源图片 | 包根目录 `.png/.jpg` 计算 dHash | 增加目录级资源聚类与近似去重 |
| Opcode 直方图 | 基于 `otool -tV` 采样（最多 10 万条）计算指令分布 | 增加按函数维度的结构相似度 |
| 启动页结构 | 当前未提取 | 增加 `.storyboardc` 结构相似度 |
| Core Data 模型 | 当前未提取 | 增加 `.xcdatamodel` 哈希与结构摘要 |

### fingerprint.json Schema

```json
{
  "meta": {
    "app_name": "Famo",
    "bundle_id": "com.ios.enterprise.famo",
    "version": "2.14.0",
    "extracted_at": "2026-03-18T16:00:00"
  },
  "binary": {
    "strings": ["..."],
    "urls": ["https://api.famo.com/v1/chat"],
    "long_strings": ["ChargeAgencyGuidePopupSceneFirstClickGame"],
    "symbols": ["PaymentManager", "GiftViewController"],
    "swift_types": ["..."],
    "frameworks": ["SDWebImage.framework", "AFNetworking.framework"],
    "opcode_histogram": {"bl": 0.23, "ldr": 0.18, "str": 0.12},
    "call_graph_hash": "abc123def456"
  },
  "extensions": [
    {
      "name": "FamoPushExtension",
      "strings": ["..."],
      "symbols": ["..."]
    }
  ],
  "private_frameworks": [
    {
      "name": "MyPrivateSDK",
      "strings": ["..."],
      "symbols": ["..."]
    }
  ],
  "resources": {
    "assets_car_names": ["room_quit", "common_avatar_sex_famale"],
    "app_icon_dhash": "f3a2b1c4d5e6f7a8",
    "lottie_files": [{"path": "gift_animation.json", "md5": "abc..."}],
    "audio_files": [{"path": "gift_sound.mp3", "md5": "def..."}],
    "fonts": [{"path": "CustomFont.ttf", "md5": "ghi..."}],
    "loose_images": [{"path": "banner.png", "dhash": "..."}]
  },
  "metadata": {
    "info_plist": {
      "permissions": {
        "NSCameraUsageDescription": "Allow camera access for video calls",
        "NSMicrophoneUsageDescription": "Allow mic access for voice calls"
      },
      "url_schemes": ["famo://"],
      "bundle_id": "com.ios.enterprise.famo",
      "min_os": "13.0"
    },
    "entitlements": {
      "app_groups": ["group.com.famo.shared"],
      "keychain_groups": ["com.famo.keychain"],
      "team_id": "ABCDEF1234"
    },
    "sdk_credentials": {
      "firebase_project_id": "famo-prod-12345",
      "google_app_id": "1:123456:ios:abcdef",
      "gcm_sender_id": "123456789",
      "facebook_app_id": "123456789012345",
      "facebook_client_token": "xxxxxxxxxxxxxxxx"
    },
    "privacy_manifest": {
      "manifests": [
        {
          "path": "PrivacyInfo.xcprivacy",
          "NSPrivacyTracking": false,
          "NSPrivacyCollectedDataTypes": []
        }
      ]
    }
  },
  "config_files": [
    {
      "path": "config/endpoints.json",
      "keys": ["api.base_url", "api.retry"],
      "sample_strings": ["https://api.example.com/v1"]
    }
  ],
  "localization": {
    "en": {"room.join": "Join Room", "gift.send": "Send Gift"},
    "ar": {"room.join": "انضم للغرفة"}
  }
}
```

---

## compare.py

比对两个指纹 JSON，输出过滤后的共同内容。

```bash
python3 scripts/compare.py \
  --a fingerprints/famo_v2.14.json \
  --b fingerprints/pyroo_v1.0.json \
  --noise noise/noise_strings.json \
  --output reports/famo_vs_pyroo_filtered.json
```

### 输出：filtered_common.json

```json
{
  "high_risk": {
    "same_team_id": true,
    "shared_sdk_credentials": ["firebase_project_id"],
    "shared_app_groups": ["group.com.famo.shared"],
    "shared_keychain_groups": ["ABCDEF1234.com.famo.keychain"],
    "common_url_schemes": ["famo"],
    "common_permission_keys": ["NSCameraUsageDescription", "NSMicrophoneUsageDescription"],
    "shared_permission_descriptions": [],
    "similar_permission_descriptions": [],
    "common_urls": ["https://api.famo.com/v1/users"],
    "common_long_strings": ["ChargeAgencyGuidePopupSceneFirstClickGame"],
    "common_swift_types": [],
    "similar_app_icon": true,
    "icon_hamming_distance": 3
  },
  "medium_risk": {
    "common_symbols": ["GiftViewController", "RoomManager"],
    "common_assets_car_names": ["room_quit", "common_avatar_sex_famale"],
    "system_common_long_strings": ["URLSession:task:didCompleteWithError:"],
    "opcode_similarity": 0.94,
    "common_lottie_md5s": [],
    "common_audio_md5s": ["2f4b3d..."],
    "framework_overlap": {
      "similarity_percentage": 72.41,
      "shared_frameworks": ["AFNetworking.framework", "SDWebImage.framework"]
    },
    "common_localization_keys": ["room.join", "gift.send"],
    "similar_loose_images": [],
    "similar_assets_car_images": []
  },
  "pending_ai_review": {
    "common_strings": [
      {
        "string": "ChargeAgencyGuidePopupSceneFirstClickGame",
        "sources_a": ["MainBinary"],
        "sources_b": ["MainBinary", "Ext:FamoPush"]
      },
      {
        "string": "RechargeSceneGiftPanel",
        "sources_a": ["FW:SudGIPWrapper"],
        "sources_b": ["FW:SudGIPWrapper"]
      }
    ],
    "count": 312
  },
  "meta": {
    "app_a": "famo_v2.14",
    "app_b": "pyroo_v1.0",
    "total_common_strings_before_filter": 26795,
    "noise_filtered_count": 26483,
    "heuristic_filtered_count": 1160,
    "total_filtered_count": 27643
  }
}
```

### 各维度比对逻辑

| 维度 | 比对方式 | 输出到 |
|------|----------|--------|
| 字符串 | 集合取交集 → 减去噪声库 | `pending_ai_review` |
| URL | 直接取交集 | `high_risk` |
| 长字符串（>30字符） | 取交集 → 减噪声 → 低信号过滤 | `high_risk.common_long_strings` / `medium_risk.system_common_long_strings` |
| 符号表 | 取交集 | `medium_risk.common_symbols` |
| Assets.car 资产名 | 取交集 | `medium_risk` |
| App 图标 | dHash 汉明距离 | ≤10 → `similar_app_icon = true` |
| Opcode 直方图 | 余弦相似度 | `opcode_similarity` 分数 |
| Team ID / SDK 凭证 | 直接值相等比较 | 匹配 → `high_risk` |
| Entitlements | key-value 比较 | 共享 group/keychain → `high_risk` |
| 权限文案 | key 取交集 + 文案相似度比对 | `high_risk.common_permission_*` |
| Lottie / 音频 | MD5 相等 | 匹配 → `medium_risk` |

---

## noise/noise_strings.json Schema

```json
{
  "_meta": {
    "generated_at": "2026-03-18",
    "pods_scanned": ["SDWebImage", "AFNetworking", "MJExtension"]
  },
  "SDWebImage": [
    "sd_setImageWithURL:",
    "SDWebImageDownloader",
    "SDWebImageErrorDownloadResponseKey"
  ],
  "MJExtension": [
    "mj_keyValues",
    "mj_JSONObject",
    "mj_keyValuesDidFinishConvertingToObject"
  ],
  "AFNetworking": [
    "AFHTTPSessionManager",
    "AFNetworkReachabilityManager"
  ]
}
```
