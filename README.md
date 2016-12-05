# 操作系统 #

    Ubuntu 14.04.2
    用户名： dejavu
    密码：p@55word

# APT源 #

    http://mirrors.aliyun.com/ubuntu/

# 安装所需软件包 #

    sudo apt-get install git

# 创建项目存放目录 #

    mkdir ~/Projects/

# 克隆veil框架和代码库 #

    cd ~/Projects
    git clone git@github.com:honovation/veil.git
    git clone git@github.com:dawncold/crowd_sorcery.git

# 生成测试环境和开发环境配置 #

    cd crowd_sorcery
    ../veil/bin/veil init
    sudo veil :test install-server
    sudo veil install-server
    veil backend database postgresql reset crowd_sorcery

# 启动开发环境 #

    sudo veil up

# 访问是否正常 #

    http://crowd.cs.dev.dmright.com

# 导入素材

    veil crowd-sorcery feature material import MATERIAL_DIR_PATH

MATERIAL_DIR_PATH的结构例如：

```
materials
├── 1990
│   ├── 1064997745.jpg
│   ├── 400x1000-4.jpg
│   └── 800x800.jpg
├── 1991
│   ├── 1136379453.jpg
│   ├── 400x1000-2.jpg
│   └── 400x1000-3.jpg
└── 1992
    ├── 1136379453.jpg
    ├── 800x800.jpg
    └── qrcode_for_gh_e986a4cd6428_430.jpg
```
