## Openai转发代理服务

### 简介

openai-relay可以一键启动转发openai请求的服务。

目前支持主流的两个接口：

1. 聊天：`/chat/completions`。
2. 向量化：`/embeddings`。



所支持的平台有：

1. openai官方以及第三方类openai。
2. 微软（azure）。
3. 百度文心一言。



项目特性：

1. fastapi异步框架。
2. redis缓存key。
3. kafka收集请求信息，异步更新token，并保存日志信息。



快速开始：

```shell
# 打包镜像，以及启动相关组件的服务，并初始化数据库。
make

# 若使用已有的服务
make build

cd deploy
# 注意修改相关服务的地址
# 启动代理服务
docker compose -f docker-compose-relay.yml up -d

# 若不启动此日志，建议将上述的yml中添加`SAVE_LOG: false`环境变量
# 启动日志异步处理服务
docker compose -f docker-compose-sync.yml up -d
```



`test`目录下有相关的调试。在正式使用前，需要添加一个可用的key，以及forward key，在`test`下面有添加脚本。







感谢项目：

[one-api: OpenAI 接口管理 & 分发系统](https://github.com/songquanpeng/one-api)

[openai-forward: 🚀 一键部署自己的AI代理 ](https://github.com/beidongjiedeguang/openai-forward)

