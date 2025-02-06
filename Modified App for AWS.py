import json
import os
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from matplotlib.font_manager import FontProperties
from flask import Flask, render_template

app = Flask(__name__)

# 資料庫配置
with open('sql.json', 'r') as file:
    db_config = json.load(file)

# 其他函數保持不變...
# [之前的 get_sensor_data 和 analyze_weekly_sensor_data 函數]

@app.route('/')
def index():
    # 獲取感測器數據
    sensor_data = get_sensor_data()
    
    # 分析數據並生成圖表
    analyze_weekly_sensor_data(sensor_data)
    
    # 渲染網頁模板
    return render_template('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)