# 使用官方的 Python 3.9 作為基礎映像
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 暴露端口（Flask 默認使用 5000）
EXPOSE 5000

# 設置環境變量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 運行應用程式
CMD ["flask", "run", "--host=0.0.0.0"]