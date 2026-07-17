import asyncio
import re
from collections import Counter
from statistics import mean
from collections.abc import AsyncIterator

from app.agents.base import AgentProvider, ResourceAgentEvent, ResourceDraft
from app.core.config import Settings
from app.schemas.learning import LearningPathDraft, LearningPathNodeDraft
from app.schemas.evaluation import (
    EvaluationDraft,
    EvaluationEvidence,
    EvaluationRecommendedChange,
    EvaluationWeakPoint,
)
from app.schemas.profile import StudentProfileData
from app.schemas.qa import AnswerMode
from app.schemas.resource import ResourceSummary, ResourceType
from app.schemas.task import GatewayEvent


# ═══════════════════════════════════════════════════════════════
# QA 图解 —— 课程知识点 → Mermaid 图解映射
# ═══════════════════════════════════════════════════════════════

# 每项: (关键词列表, 图解标题, Mermaid 代码, 文字解释摘要)
_QA_DIAGRAM_TOPICS: list[tuple[list[str], str, str, str]] = [
    (
        ["ros", "发布", "订阅", "话题", "节点", "通信", "turtle", "小乌龟", "publisher", "subscriber", "topic"],
        "ROS 发布-订阅通信架构",
        """graph TD
    A["🎓 ROS Master<br/>节点注册与发现"] --> B["📤 Publisher Node<br/>发布者节点"]
    A --> C["📥 Subscriber Node<br/>订阅者节点"]
    B --> D["📨 Topic: /cmd_vel<br/>话题：速度指令"]
    D --> C
    B --> E["📨 Topic: /sensor_data<br/>话题：传感器数据"]
    E --> C
    style A fill:#edf3ff,stroke:#2457d6,color:#182132
    style B fill:#f4f9ea,stroke:#55741f,color:#27344a
    style C fill:#f4f9ea,stroke:#55741f,color:#27344a
    style D fill:#fff3d9,stroke:#8a5b05,color:#27344a
    style E fill:#fff3d9,stroke:#8a5b05,color:#27344a""",
        "ROS 采用**发布-订阅**模式解耦节点间通信。发布者（Publisher）将消息发送到特定**话题（Topic）**，订阅者（Subscriber）监听感兴趣的话题并接收消息。ROS Master 负责节点的注册与发现，节点之间不直接通信，从而实现了高度的模块化和灵活性。",
    ),
    (
        ["arp", "arp 欺骗", "arp 中毒", "spoofing", "地址解析", "mac 欺骗"],
        "ARP 欺骗攻击流程",
        """sequenceDiagram
    participant A as 🖥️ 受害者主机
    participant B as ⚠️ 攻击者
    participant C as 🌐 网关/路由器
    Note over A,C: 正常通信：A ↔ 网关 ↔ 互联网
    B->>A: 伪造 ARP 响应：「网关 IP 的 MAC 是我！」
    A->>A: 更新 ARP 缓存表（错误映射）
    B->>C: 伪造 ARP 响应：「A 的 MAC 是我！」
    C->>C: 更新 ARP 缓存表（错误映射）
    Note over A,C: ⚠️ 攻击者已插入通信链路
    A->>B: 发往网关的数据包（被劫持）
    B->>C: 转发给网关（可篡改/窃听）
    C->>B: 网关回复（被劫持）
    B->>A: 转发给受害者（可篡改/窃听）
    Note over A,C: 🛡️ 防护：静态 ARP 绑定 / ARP 检测工具""",
        "ARP 欺骗（ARP Spoofing）是链路层攻击手法。攻击者向局域网发送**伪造的 ARP 响应**，将网关 IP 映射到攻击者 MAC 地址，使受害者流量经过攻击者主机，从而实现**流量劫持、窃听或篡改**。",
    ),
    (
        ["mitm", "中间人攻击", "流量劫持", "篡改", "数据窃听"],
        "中间人攻击（MITM）核心链路",
        """sequenceDiagram
    participant V as 🎯 受害者
    participant M as ⚠️ 中间人（攻击者）
    participant S as 🖥️ 目标服务器
    Note over V,S: 受害者以为在与服务器直接通信
    V->>M: ① 建立连接（被截获）
    M->>S: ② 攻击者伪装受害者连接服务器
    S->>M: ③ 服务器响应
    M->>V: ④ 攻击者转发（可能已篡改）
    Note over V,S: 🔍 攻击者可以：<br/>- 窃听明文数据<br/>- 篡改通信内容<br/>- 注入恶意代码<br/>- 劫持会话 Cookie
    Note over V,S: 🛡️ 防护：TLS 加密 / 证书校验 / HSTS""",
        "中间人攻击（MITM）将攻击者插入通信双方之间，使双方以为在直接通信，实际上所有数据流经攻击者。结合 ARP 欺骗可在局域网实现；结合 DNS 劫持可在广域网实现。**TLS/HTTPS + 证书校验**是最核心的防护手段。",
    ),
    (
        ["dos", "拒绝服务", "ddos", "泛洪", "flood", "拒绝服务攻击"],
        "DOS 拒绝服务攻击示意",
        """graph TD
    A["⚔️ 攻击者<br/>（或僵尸网络）"] --> B["📨 大量恶意请求<br/>SYN Flood / HTTP Flood"]
    B --> C["🖥️ 目标服务器<br/>资源耗尽"]
    C --> D{"资源状态"}
    D -->|"CPU 100%"| E["❌ 无法响应正常请求"]
    D -->|"带宽占满"| E
    D -->|"连接池耗尽"| E
    F["👤 正常用户"] -->|"合法请求"| C
    F -->|"被拒绝"| G["⛔ 服务不可用"]
    style A fill:#fde8e8,stroke:#c7463c,color:#8b3a2c
    style C fill:#fff3d9,stroke:#8a5b05,color:#27344a
    style E fill:#fde8e8,stroke:#c7463c,color:#8b3a2c
    style G fill:#fde8e8,stroke:#c7463c,color:#8b3a2c""",
        "拒绝服务攻击（DOS/DDOS）通过**耗尽目标系统资源**使其无法为正常用户提供服务。常见手法包括 SYN Flood（半连接耗尽）、HTTP Flood（应用层泛洪）和放大攻击。防护措施包括流量清洗、速率限制和 CDN 分散。",
    ),
    (
        ["rsa", "加密", "密码", "公钥", "私钥", "通信安全", "crypto"],
        "RSA 非对称加密通信流程",
        """sequenceDiagram
    participant A as 👤 发送方 Alice
    participant B as 👤 接收方 Bob
    Note over B: 🔑 Bob 生成密钥对<br/>公钥 Public Key + 私钥 Private Key
    B->>A: 📬 分发公钥（可公开）
    Note over A: 📝 Alice 用 Bob 的公钥<br/>加密明文消息
    A->>B: 🔒 发送密文（只有私钥能解密）
    Note over B: 🔓 Bob 用私钥解密<br/>恢复明文消息
    Note over A,B: ⚡ 实际应用中：<br/>RSA 加密对称密钥 →<br/>对称密钥加密数据（混合加密）
    Note over A,B: 🛡️ 安全性依赖大整数分解难题""",
        "RSA 是经典的**非对称加密**算法。通信前接收方生成公钥/私钥对，发送方使用公钥加密，只有持有私钥的接收方能解密。实际工程中常采用**混合加密**：RSA 交换会话密钥，AES 等对称算法加密数据体。",
    ),
    (
        ["slam", "导航", "地图", "定位", "建图", "路径规划", "激光"],
        "SLAM 地图构建与导航流水线",
        """graph LR
    A["📡 传感器数据<br/>激光雷达 / 摄像头 / IMU"] --> B["🧭 前端里程计<br/>帧间匹配 / 位姿估计"]
    B --> C["🗺️ 后端优化<br/>图优化 / 回环检测"]
    C --> D["📋 栅格地图<br/>占据栅格 / 代价地图"]
    D --> E["🎯 全局规划器<br/>A* / Dijkstra 全局路径"]
    E --> F["🚗 局部规划器<br/>DWA / TEB 动态避障"]
    F --> G["⚙️ 控制指令<br/>cmd_vel 下发"]
    style A fill:#edf3ff,stroke:#2457d6,color:#182132
    style C fill:#f4f9ea,stroke:#55741f,color:#27344a
    style D fill:#fff3d9,stroke:#8a5b05,color:#27344a
    style G fill:#edf3ff,stroke:#2457d6,color:#182132""",
        "SLAM（同时定位与建图）是机器人自主导航的核心。传感器数据经**前端里程计**估计位姿，**后端优化**消除累计误差并检测回环，最终构建**栅格/代价地图**供全局与局部规划器使用，生成运动控制指令。",
    ),
    (
        ["多机", "编队", "多机器人", "协同", "formation", "集群"],
        "多机器人编队协同架构",
        """graph TD
    A["🖥️ 中央协调节点<br/>编队控制器"] --> B["🤖 机器人 1<br/>Leader / Follower"]
    A --> C["🤖 机器人 2<br/>Follower"]
    A --> D["🤖 机器人 3<br/>Follower"]
    B <-->|"📡 相对位姿 / 速度同步"| C
    B <-->|"📡 相对位姿 / 速度同步"| D
    C <-->|"📡 队形保持"| D
    E["📋 预设队形<br/>V形 / 横队 / 纵队"] --> A
    F["🚧 障碍物感知"] --> A
    A --> G["⚙️ 各机器人 cmd_vel"]
    style A fill:#edf3ff,stroke:#2457d6,color:#182132
    style B fill:#f4f9ea,stroke:#55741f,color:#27344a
    style C fill:#f4f9ea,stroke:#55741f,color:#27344a
    style D fill:#f4f9ea,stroke:#55741f,color:#27344a
    style E fill:#fff3d9,stroke:#8a5b05,color:#27344a""",
        "多机器人编队通过**Leader-Follower**或虚拟结构法协调多台机器人形成并保持预设队形。各机器人实时交换位姿信息，中央协调节点根据队形偏差和环境障碍动态调整每个机器人的速度指令。",
    ),
    (
        ["实验环境", "虚拟机", "网络拓扑", "环境配置", "拓扑", "环境搭建", "vm"],
        "课程实验网络拓扑",
        """graph TD
    A["🖥️ 宿主机<br/>Windows / Linux"] --> B["📦 虚拟机 VM<br/>Ubuntu + ROS"]
    B --> C["🐢 Turtlesim<br/>仿真环境"]
    B --> D["🤖 真实机器人<br/>TurtleBot / 自研"]
    D --> E["📡 传感器<br/>激光雷达 / 摄像头"]
    D --> F["⚙️ 执行器<br/>电机 / 舵机"]
    G["🌐 实验网络<br/>192.168.x.x"] --> B
    G --> H["🖥️ 攻击机<br/>Kali / 渗透工具"]
    G --> I["🛡️ 靶机<br/>安全实验目标"]
    style A fill:#edf3ff,stroke:#2457d6,color:#182132
    style B fill:#f4f9ea,stroke:#55741f,color:#27344a
    style G fill:#fff3d9,stroke:#8a5b05,color:#27344a
    style H fill:#fde8e8,stroke:#c7463c,color:#8b3a2c""",
        "实验环境由宿主机、Ubuntu 虚拟机、ROS 框架和机器人硬件组成。网络攻防实验中另有攻击机和靶机节点。理解网络拓扑是后续 ARP、MITM、DOS 等实验的基础。",
    ),
    (
        ["暴力破解", "brute force", "密码破解", "字典攻击", "穷举"],
        "暴力破解攻击流程",
        """graph TD
    A["👤 攻击者"] --> B["📋 加载密码字典<br/>常见弱密码 / 泄露库"]
    B --> C{"🔄 尝试登录<br/>目标服务（SSH/FTP/Web）"}
    C -->|"❌ 失败"| D["⏱️ 等待间隔<br/>规避账户锁定"]
    D --> C
    C -->|"✅ 成功"| E["🔓 获取访问权限"]
    F["🛡️ 防护措施"] --> G["强密码策略"]
    F --> H["多因素认证 MFA"]
    F --> I["失败次数限制"]
    F --> J["账户锁定机制"]
    style C fill:#fff3d9,stroke:#8a5b05,color:#27344a
    style E fill:#fde8e8,stroke:#c7463c,color:#8b3a2c
    style F fill:#edf3ff,stroke:#2457d6,color:#182132""",
        "暴力破解通过**穷举或字典遍历**尝试所有可能的密码组合。攻击者常利用弱密码和泄露密码库提高成功率。防护核心是**强密码策略 + 多因素认证 + 失败次数限制**。",
    ),
    (
        ["循线", "跟踪", "传感器", "巡线", "line follow", "红外"],
        "机器人循线跟踪控制回路",
        """graph LR
    A["📷 传感器<br/>红外 / 摄像头"] --> B["📊 线位偏差计算<br/>左偏 / 右偏 / 居中"]
    B --> C["🧠 PID 控制器<br/>P: 比例调节<br/>D: 微分阻尼"]
    C --> D["⚙️ 差速驱动<br/>左轮减速 / 右轮加速"]
    D --> E["🤖 机器人姿态修正"]
    E --> A
    F["📐 参考线<br/>黑线 / 白色背景"] -.-> A
    style C fill:#edf3ff,stroke:#2457d6,color:#182132
    style D fill:#f4f9ea,stroke:#55741f,color:#27344a
    style F fill:#fff3d9,stroke:#8a5b05,color:#27344a""",
        "循线跟踪是一个经典的**闭环控制**问题。传感器检测线位偏差，PID 控制器计算差速修正量，实时调整机器人姿态使传感器始终对准参考线。核心在于 PID 参数的在线或离线整定。",
    ),
]

# 默认兜底图解 —— 课程知识体系概览
_DEFAULT_DIAGRAM: tuple[str, str, str] = (
    "「机器人与安全」课程知识体系",
    """mindmap
  root((机器人与安全))
    基础准备
      课程导论与实验总览
      虚拟机与实验环境配置
      网络环境与基础连通性
    ROS 与机器人控制
      实验一：ROS 进阶与小乌龟
      实验二：机器人连接与远程控制
      实验三：SLAM 地图构建与导航
      实验四：机器人循线跟踪
    网络攻防实战
      实验五：ARP 中毒攻击
      实验六：中间人攻击 MITM
      实验七：DOS 拒绝服务攻击
      实验十：暴力破解攻击
    密码与通信安全
      实验八：RSA 加密与通讯
    视觉与高级应用
      实验九：双目视觉摄像头攻击
      实验十一：多机编队实验
    拓展资源
      课程参考书与手册
      实验代码仓库
      在线学习社区""",
    "本课程「机器人与安全」覆盖**ROS 机器人控制**与**网络安全攻防**两大主线。从环境搭建、ROS 入门开始，逐步深入到 SLAM 导航、循线控制，再过渡到 ARP 欺骗、MITM、DOS 等网络攻防实验，最后以 RSA 加密和多机编队综合实验收尾。",
)


# ═══════════════════════════════════════════════════════════════
# 薄弱点概念映射 —— 把原始错题/提问文本归纳为知识点概念
# ═══════════════════════════════════════════════════════════════
# 每项: (关键词列表, 知识点概念名, 薄弱点原因描述)
_WEAK_POINT_CONCEPTS: list[tuple[list[str], str, str]] = [
    (
        ["ros", "ros2", "发布", "订阅", "话题", "节点", "通信", "turtle", "小乌龟",
         "publisher", "subscriber", "topic", "rclpy", "机器人操作系统"],
        "ROS 通信机制",
        "对 ROS 节点发布/订阅模型、话题通信、消息传递及 Master 注册发现机制的综合理解存在薄弱点",
    ),
    (
        ["arp", "欺骗", "spoofing", "地址解析", "arp 中毒", "mac 欺骗", "mac地址"],
        "ARP 欺骗攻击与防御",
        "对 ARP 协议工作流程及其欺骗原理的理解不深，容易混淆正常 ARP 解析与伪造 ARP 响应的区别",
    ),
    (
        ["mitm", "中间人攻击", "流量劫持", "篡改", "数据窃听"],
        "中间人攻击（MITM）",
        "对中间人攻击的劫持链路、流量篡改手段及数据窃听风险的系统性理解存在薄弱点",
    ),
    (
        ["dos", "ddos", "拒绝服务", "泛洪", "flood", "syn", "服务不可用"],
        "拒绝服务攻击与防护",
        "对 DOS/DDOS 攻击原理、常见泛洪手法和防御策略的理解不够系统",
    ),
    (
        ["rsa", "加密", "密码", "公钥", "私钥", "非对称", "crypto", "解密"],
        "RSA 加密与安全通信",
        "对非对称加密原理、RSA 密钥对生成过程及混合加密体系的理解存在薄弱点",
    ),
    (
        ["slam", "导航", "地图", "定位", "建图", "路径规划", "激光", "栅格", "代价地图"],
        "SLAM 与自主导航",
        "对 SLAM 定位建图流水线、全局/局部路径规划及代价地图概念的理解不够清晰",
    ),
    (
        ["多机", "编队", "多机器人", "协同", "formation", "集群", "leader", "follower"],
        "多机器人编队协同",
        "对多机编队协同控制架构、Leader-Follower 模式及队形保持机制的理解存在薄弱点",
    ),
    (
        ["循线", "跟踪", "巡线", "line follow", "红外", "pid", "差速", "控制回路"],
        "机器人循线跟踪控制",
        "对循线传感器信号处理、PID 控制回路及差速驱动修正机制的综合理解不够深入",
    ),
    (
        ["暴力破解", "brute force", "密码破解", "字典攻击", "穷举", "弱密码", "认证"],
        "暴力破解与认证安全",
        "对暴力破解攻击方式、字典攻击原理及认证安全防护措施的理解不够系统",
    ),
    (
        ["实验环境", "虚拟机", "网络拓扑", "环境配置", "拓扑", "环境搭建", "vm", "ubuntu"],
        "实验环境与网络配置",
        "对虚拟机环境搭建、实验网络拓扑和基础连通性配置的理解还不够熟练",
    ),
    (
        ["双目", "视觉", "摄像头", "图像识别", "视觉感知", "识别攻击"],
        "视觉感知与安全",
        "对双目视觉原理、摄像头识别攻击面及视觉安全边界的理解存在薄弱点",
    ),
    (
        ["远程控制", "连接", "远程", "telnet", "ssh", "远程登录"],
        "机器人远程控制",
        "对机器人远程连接流程、指令下发机制和基础调试方法的理解不够熟练",
    ),
]

# 无匹配时的兜底概念
_FALLBACK_CONCEPT: tuple[str, str] = (
    "课程核心知识点",
    "该薄弱项涉及课程核心内容，建议通过复习讲义和追加练习来巩固",
)


def _conceptualize_weak_point(text: str) -> tuple[str, str]:
    """把原始错题/提问文本映射为知识点概念名和原因描述。

    返回 (概念名, 薄弱点原因描述)。

    示例：
        "ROS2 节点通信中，发布端通常通过什么方式发送消息？"
        → ("ROS 通信机制", "对 ROS 节点发布/订阅模型...")
    """
    lowered = text.lower()
    best_score = 0
    best_concept = _FALLBACK_CONCEPT
    for keywords, concept_name, error_summary in _WEAK_POINT_CONCEPTS:
        score = sum(1 for kw in keywords if kw in lowered)
        if score > best_score:
            best_score = score
            best_concept = (concept_name, error_summary)
    return best_concept


# ═══════════════════════════════════════════════════════════════
# 知识点概念 → 知识库目录 ID 映射（用于视频推送）
# ═══════════════════════════════════════════════════════════════
_TOPIC_TO_KP_ID: dict[str, str] = {
    "ROS 通信机制": "exp01_ros_turtlesim",
    "机器人远程控制": "exp02_robot_remote_control",
    "SLAM 与自主导航": "exp03_slam_mapping_navigation",
    "机器人循线跟踪控制": "exp04_line_following",
    "ARP 欺骗攻击与防御": "exp05_arp_poisoning",
    "中间人攻击（MITM）": "exp06_mitm_attack",
    "拒绝服务攻击与防护": "exp07_dos_attack",
    "RSA 加密与安全通信": "exp08_rsa_communication",
    "视觉感知与安全": "exp09_stereo_vision_attack",
    "暴力破解与认证安全": "exp10_brute_force_attack",
    "多机器人编队协同": "exp11_multi_robot_formation",
    "实验环境与网络配置": "vm_environment_setup",
}

# 默认课程 slug
_DEFAULT_COURSE_SLUG = "robot-safety"

_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}


def _find_course_video(course_root, question: str) -> tuple[str | None, str, str]:
    """在课程数据目录中查找与问题匹配的视频文件。

    Args:
        course_root: 课程数据根目录 (Path)
        question: 学生提问文本

    Returns:
        (video_url, topic_title, intro_text) —
        video_url 可能为 None（无匹配视频时）。
    """
    from urllib.parse import quote

    # 用概念映射（与评估薄弱点一致）匹配知识点概念名
    concept, _ = _conceptualize_weak_point(question)
    kp_id = _TOPIC_TO_KP_ID.get(concept)
    if kp_id is None:
        return (None, concept, f"知识点「{concept}」暂无对应的实验视频目录。")

    kp_dir = course_root / _DEFAULT_COURSE_SLUG / kp_id
    if not kp_dir.is_dir():
        return (None, concept, f"知识点「{concept}」的素材目录尚未同步。")

    videos: list[tuple] = []  # (filename, path)
    for f in sorted(kp_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in _VIDEO_EXTENSIONS:
            videos.append((f.name, f))

    if not videos:
        return (None, concept, f"知识点「{concept}」暂无实验演示视频。")

    # 优先选带"新_"前缀的视频（更新版本），否则取第一个
    preferred = None
    for name, path in videos:
        if name.startswith("新_"):
            preferred = (name, path)
            break
    if preferred is None:
        preferred = videos[0]

    filename, _ = preferred
    url = f"/media/courses/{_DEFAULT_COURSE_SLUG}/{quote(kp_id)}/{quote(filename)}"
    intro = f"为你找到关于「{concept}」的实验演示视频：**{filename}**\n\n"
    return (url, concept, intro)


class MockAgentProvider(AgentProvider):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def stream_profile(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        chat_text: str,
        current_profile: StudentProfileData | None,
    ) -> AsyncIterator[GatewayEvent]:
        profile = StudentProfileData(
            knowledge_foundation="具备入门基础，需要通过结构化练习巩固概念。",
            cognitive_style="偏好案例驱动与步骤化讲解。",
            weak_points=[chat_text.strip()[:80]],
            learning_pace="分阶段推进，每个阶段包含讲解与练习。",
            content_preferences=["图解", "代码案例"],
            short_term_goal="完成当前课程薄弱知识点的强化学习。",
        )
        events = [
            GatewayEvent(
                event="task.started",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="主管Agent",
                progress=0,
                demo_mode=True,
            ),
            GatewayEvent(
                event="agent.started",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="画像抽取Agent",
                progress=10,
                demo_mode=True,
            ),
            GatewayEvent(
                event="content.delta",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="画像抽取Agent",
                progress=35,
                content="正在理解你的学习背景，",
                demo_mode=True,
            ),
            GatewayEvent(
                event="content.delta",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="画像抽取Agent",
                progress=60,
                content="画像的六个维度已完成本轮更新。",
                demo_mode=True,
            ),
            GatewayEvent(
                event="profile.patch",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="画像抽取Agent",
                progress=85,
                profile_patch=profile.model_dump(),
                demo_mode=True,
            ),
            GatewayEvent(
                event="task.completed",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="画像抽取Agent",
                progress=100,
                finish_flag=True,
                demo_mode=True,
            ),
        ]

        for index, event in enumerate(events):
            yield event
            if self.settings.mock_event_delay_ms and index < len(events) - 1:
                await asyncio.sleep(self.settings.mock_event_delay_ms / 1000)

    async def stream_resources(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        course_name: str,
        weak_point: str,
        resource_types: list[ResourceType],
    ) -> AsyncIterator[ResourceAgentEvent]:
        for index, resource_type in enumerate(resource_types):
            agent = self._resource_agent_name(resource_type)
            progress = min(95, 8 + index * max(1, 82 // max(1, len(resource_types))))
            yield ResourceAgentEvent(
                event="agent.started",
                current_agent=agent,
                progress=progress,
                resource_type=resource_type,
            )
            if self.settings.mock_event_delay_ms:
                await asyncio.sleep(self.settings.mock_event_delay_ms / 1000)

            yield ResourceAgentEvent(
                event="content.delta",
                current_agent=agent,
                progress=min(97, progress + 8),
                resource_type=resource_type,
                content=f"正在生成 {resource_type} 演示资源。",
            )
            if self.settings.mock_event_delay_ms:
                await asyncio.sleep(self.settings.mock_event_delay_ms / 1000)

            yield ResourceAgentEvent(
                event="resource.ready",
                current_agent=agent,
                progress=min(99, progress + 14),
                resource_type=resource_type,
                resource=self._resource_draft(
                    resource_type=resource_type,
                    course_name=course_name,
                    weak_point=weak_point,
                ),
            )
            if self.settings.mock_event_delay_ms and index < len(resource_types) - 1:
                await asyncio.sleep(self.settings.mock_event_delay_ms / 1000)

    @staticmethod
    def _resource_agent_name(resource_type: ResourceType) -> str:
        return {
            "handout": "讲义编写Agent",
            "mindmap": "思维导图Agent",
            "quiz": "题库Agent",
            "code": "代码案例Agent",
            "video": "多模态素材Agent",
        }[resource_type]

    @staticmethod
    def _resource_draft(
        *, resource_type: ResourceType, course_name: str, weak_point: str
    ) -> ResourceDraft:
        title = f"演示资源 · {course_name} · {weak_point or '核心知识点'}"
        if resource_type == "handout":
            return ResourceDraft(
                resource_type=resource_type,
                title=f"{title}讲义",
                payload={
                    "markdown": (
                        f"# {course_name}\n\n"
                        f"## 聚焦知识点\n\n{weak_point or '核心知识点'}\n\n"
                        "## 学习步骤\n\n1. 建立概念模型\n2. 阅读代码示例\n3. 完成针对性练习"
                    )
                },
            )
        if resource_type == "mindmap":
            return ResourceDraft(
                resource_type=resource_type,
                title=f"{title}思维导图",
                payload={
                    "nodes": [
                        {"id": "root", "label": course_name, "parent_id": None},
                        {"id": "focus", "label": weak_point or "核心知识点", "parent_id": "root"},
                        {"id": "practice", "label": "练习验证", "parent_id": "focus"},
                    ]
                },
            )
        if resource_type == "quiz":
            return ResourceDraft(
                resource_type=resource_type,
                title=f"{title}题库",
                payload={
                    "questions": [
                        {
                            "id": "q1",
                            "question_type": "choice",
                            "prompt": "ROS2 节点通信中，发布端通常通过什么方式发送消息？",
                            "options": ["A", "B", "C", "D"],
                            "answer": "B",
                            "explanation": "演示题使用 B 作为正确选项。",
                        },
                        {
                            "id": "q2",
                            "question_type": "blank",
                            "prompt": "ROS2 的运行单元称为____。",
                            "options": [],
                            "answer": "节点",
                            "explanation": "节点是 ROS2 应用的基本运行单元。",
                        },
                        {
                            "id": "q3",
                            "question_type": "programming",
                            "prompt": "写出发布消息的核心调用。",
                            "options": [],
                            "answer": "publisher.publish(message)",
                            "explanation": "演示评分比较规范化后的期望输出。",
                        },
                    ]
                },
            )
        if resource_type == "code":
            return ResourceDraft(
                resource_type=resource_type,
                title=f"{title}代码案例",
                payload={
                    "language": "python",
                    "description": "ROS2 发布节点最小示例。",
                    "code": (
                        "import rclpy\n\n"
                        "def publish_once(publisher, message):\n"
                        "    publisher.publish(message)\n"
                    ),
                },
            )
        return ResourceDraft(
            resource_type="video",
            title=f"{title}视频讲解",
            payload={
                "summary": "等待真实多模态 Agent 返回教学视频链接后即可预览。",
                "poster_url": "",
                "duration_seconds": 180,
            },
            media_url=None,
        )

    async def build_learning_path(
        self,
        *,
        user_id: str,
        course_name: str,
        profile: StudentProfileData,
        resources: list[ResourceSummary],
    ) -> LearningPathDraft:
        resource_by_type = {resource.resource_type: resource.id for resource in resources}
        return LearningPathDraft(
            nodes=[
                LearningPathNodeDraft(
                    stage_name="基础补全",
                    difficulty="基础",
                    resource_id=resource_by_type.get("handout"),
                ),
                LearningPathNodeDraft(
                    stage_name="知识点学习",
                    difficulty="进阶",
                    resource_id=resource_by_type.get("mindmap")
                    or resource_by_type.get("handout"),
                ),
                LearningPathNodeDraft(
                    stage_name="习题训练",
                    difficulty="巩固",
                    resource_id=resource_by_type.get("quiz"),
                ),
                LearningPathNodeDraft(
                    stage_name="代码实操",
                    difficulty="实操",
                    resource_id=resource_by_type.get("code"),
                ),
                LearningPathNodeDraft(
                    stage_name="拓展视频",
                    difficulty="拓展",
                    resource_id=resource_by_type.get("video"),
                ),
            ]
        )

    @staticmethod
    def _match_qa_topic(question: str) -> tuple[str, str, str]:
        """根据学生提问匹配最相关的课程知识点图解。

        返回 (图解标题, Mermaid 代码, 文字解释) 三元组。
        无匹配时返回默认课程概览思维导图。
        """
        lowered = question.lower()
        best_score = 0
        best = _DEFAULT_DIAGRAM
        for keywords, title, diagram, explanation in _QA_DIAGRAM_TOPICS:
            score = sum(1 for kw in keywords if kw in lowered)
            if score > best_score:
                best_score = score
                best = (title, diagram, explanation)
        return best

    @staticmethod
    def _qa_text_parts(
        question: str,
        profile: StudentProfileData,
        diagram_title: str,
        explanation: str,
    ) -> list[str]:
        """构建 QA 文字增量（content.delta 的 content 片段）。"""
        cognitive_hint = {
            "偏好案例驱动与步骤化讲解。": "我会结合具体案例和分步骤的图解来讲解。",
            "偏好理论推导与公式推演。": "我会从原理和机制层面为你分析。",
        }.get(profile.cognitive_style, "我会按你的学习偏好来解释。")

        return [
            f"🤔 你的问题与 **{diagram_title}** 相关，{cognitive_hint}\n\n",
            f"{explanation}\n\n",
        ]

    @staticmethod
    def _qa_diagram_markdown(title: str, mermaid_code: str) -> str:
        """将 Mermaid 图解包装为 Markdown 代码块。"""
        return (
            f"### 📊 图解：{title}\n\n"
            f"```mermaid\n{mermaid_code}\n```\n\n"
            f"> 上图展示了 **{title}** 的核心结构与关键流程。"
            f"你可以结合文字解释一起理解。\n\n"
        )

    async def stream_qa(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        question: str,
        answer_mode: AnswerMode,
        profile: StudentProfileData,
    ) -> AsyncIterator[GatewayEvent]:
        diagram_title, mermaid_code, explanation = self._match_qa_topic(question)
        text_parts = self._qa_text_parts(question, profile, diagram_title, explanation)
        use_diagram = answer_mode == "image"

        events: list[GatewayEvent] = [
            GatewayEvent(
                event="agent.started",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="智能答疑Agent",
                progress=10,
                demo_mode=True,
            ),
            GatewayEvent(
                event="content.delta",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="智能答疑Agent",
                progress=30,
                content=text_parts[0],
                demo_mode=True,
            ),
        ]

        # 图解模式：在文字解释段落后插入 Mermaid 图解
        if use_diagram:
            diagram_md = self._qa_diagram_markdown(diagram_title, mermaid_code)
            events.append(
                GatewayEvent(
                    event="content.delta",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent="智能答疑Agent",
                    progress=55,
                    content=text_parts[1] + diagram_md,
                    demo_mode=True,
                )
            )
        else:
            events.append(
                GatewayEvent(
                    event="content.delta",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent="智能答疑Agent",
                    progress=55,
                    content=text_parts[1],
                    demo_mode=True,
                )
            )

        events.append(
            GatewayEvent(
                event="content.delta",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="智能答疑Agent",
                progress=80,
                content=(
                    "如果你还有疑问，可以继续追问，我会进一步为你解释。\n\n"
                    "💡 **提示**：你也可以切换到「纯文字」或「短视频讲解」模式获取不同形式的解答。"
                ),
                demo_mode=True,
            )
        )

        # 视频模式：从课程数据目录查找真实视频文件
        if answer_mode == "video":
            video_url, video_topic, video_intro = _find_course_video(
                self.settings.course_root, question
            )
            if video_url is not None:
                events.append(
                    GatewayEvent(
                        event="content.delta",
                        task_id=task_id,
                        trace_id=trace_id,
                        current_agent="智能答疑Agent",
                        progress=85,
                        content=f"\n\n{video_intro}",
                        demo_mode=True,
                    )
                )
                events.append(
                    GatewayEvent(
                        event="media.ready",
                        task_id=task_id,
                        trace_id=trace_id,
                        current_agent="智能答疑Agent",
                        progress=92,
                        resource_type="video",
                        media_url=video_url,
                        content=f"实验演示视频：{video_topic}",
                        demo_mode=True,
                    )
                )
            else:
                events.append(
                    GatewayEvent(
                        event="content.delta",
                        task_id=task_id,
                        trace_id=trace_id,
                        current_agent="智能答疑Agent",
                        progress=88,
                        content=f"\n\n{video_intro}",
                        demo_mode=True,
                    )
                )

        events.append(
            GatewayEvent(
                event="task.completed",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="智能答疑Agent",
                progress=100,
                finish_flag=True,
                demo_mode=True,
            )
        )

        for index, event in enumerate(events):
            yield event
            if self.settings.mock_event_delay_ms and index < len(events) - 1:
                await asyncio.sleep(self.settings.mock_event_delay_ms / 1000)

    async def build_evaluation(
        self,
        *,
        user_id: str,
        course_name: str,
        evidence: EvaluationEvidence,
    ) -> EvaluationDraft:
        theory_score = (
            round(mean(attempt.score for attempt in evidence.attempts))
            if evidence.attempts
            else 0
        )
        completed_practice = sum(node.completed for node in evidence.practice_nodes)
        practice_score = round(
            100 * completed_practice / max(len(evidence.practice_nodes), 1)
        )

        # ── 薄弱点归纳：原始错题文本 → 概念型知识点 ──
        weak_counter: Counter[str] = Counter()
        # 每个概念对应的代表性原因描述（取首次匹配到的）
        concept_reasons: dict[str, str] = {}
        for attempt in evidence.attempts:
            for point in attempt.incorrect_points:
                concept, reason = _conceptualize_weak_point(point)
                weak_counter[concept] += 1
                concept_reasons.setdefault(concept, reason)
        for point in evidence.question_weak_points:
            concept, reason = _conceptualize_weak_point(point)
            weak_counter[concept] += 1
            concept_reasons.setdefault(concept, reason)

        weak_points = [
            EvaluationWeakPoint(name=concept, frequency=frequency)
            for concept, frequency in sorted(
                weak_counter.items(), key=lambda item: (-item[1], item[0])
            )[:6]
        ]

        recommended_changes = []
        for weak_point in weak_points[:3]:
            reason_detail = concept_reasons.get(
                weak_point.name,
                f"该薄弱项在学习证据中出现 {weak_point.frequency} 次。",
            )
            recommended_changes.append(
                EvaluationRecommendedChange(
                    stage_name=f"{weak_point.name} 强化训练",
                    difficulty="巩固",
                    reason=f"薄弱点「{weak_point.name}」出现 {weak_point.frequency} 次。{reason_detail}。",
                    resource_id=evidence.quiz_resource_id,
                )
            )
        if not recommended_changes and any(
            not node.completed for node in evidence.practice_nodes
        ):
            recommended_changes.append(
                EvaluationRecommendedChange(
                    stage_name="代码实操强化",
                    difficulty="实操",
                    reason="当前学习路径仍有未完成的实操节点。",
                )
            )

        return EvaluationDraft(
            theory_score=theory_score,
            practice_score=practice_score,
            weak_points=weak_points,
            recommended_changes=recommended_changes,
        )
