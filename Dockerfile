# 使用 Python 3.12 作為基礎鏡像
FROM python:3.12-slim

# 設置工作目錄
WORKDIR /app

# 複製當前目錄內容到容器中的 /app
COPY . /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 安裝所需的 Python 包
RUN pip install --no-cache-dir -r requirements.txt

# 設置環境變量
# 請自行設置環境變量
# ENV OPENROUTER_API_KEY=your_openrouter_api_key
ENV OPENROUTER_MODEL=anthropic/claude-4.5-sonnet
ENV OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions

# 暴露 Gradio 默認端口
EXPOSE 7860

# 運行應用
CMD ["python", "src/ui.py"]