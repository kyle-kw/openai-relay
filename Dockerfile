FROM python:3.9.17-buster as builder
ENV TZ='Asia/Shanghai' PYTHONUNBUFFERED='1' PYTHONIOENCODING='utf-8'

WORKDIR /app

COPY ./requirements.txt requirements.txt

RUN pip install -r requirements.txt

FROM python:3.9-slim

# 从构建阶段1中复制必要的文件
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# 设置环境变量
ENV PYTHONPATH=/usr/local/lib/python3.9/site-packages:/app

RUN python -c "import tiktoken;print(tiktoken.encoding_for_model('gpt-3.5-turbo').encode('1'))"

WORKDIR /app
COPY app/ app

ENTRYPOINT ["python", "app/__main__.py", "run"]

# docker build . -t openai-relay:0.0.1
