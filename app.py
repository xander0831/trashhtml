import json
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

def get_sensor_data():
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            print("成功連接到資料庫")
            
        cursor = conn.cursor()
        
        # 獲取所有數據並按日期排序
        query = """
        SELECT identify_time, results 
        FROM sensor 
        ORDER BY identify_time DESC
        LIMIT 100
        """
        cursor.execute(query)
        data = cursor.fetchall()
        print(f"獲取到的數據筆數: {len(data)}")
        
        df = pd.DataFrame(data, columns=['identify_time', 'results'])
        return df
        
    except Exception as e:
        print(f"發生錯誤: {e}")
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("資料庫連接已關閉")

def analyze_weekly_sensor_data(df):
    if df is None or df.empty:
        print("沒有資料可供分析")
        return None
        
    # 設定中文字型
    font = FontProperties(fname='SimHei.ttf')
    
    # 確保 identify_time 是日期時間格式
    df['identify_time'] = pd.to_datetime(df['identify_time'])
    df['date'] = df['identify_time'].dt.date
    
    # 計算每天的滿的次數
    daily_counts = df[df['results'] == '滿'].groupby('date').size()
    
    # 只取最新的7天數據
    daily_counts = daily_counts.sort_index(ascending=False).head(7)
    daily_counts = daily_counts.sort_index()
    
    print("每日統計:", daily_counts)
    
    # 創建折線圖
    plt.figure(figsize=(12, 6))
    
    # 設定較小的y軸範圍
    max_count = daily_counts.max()
    y_max = max_count + 1 if max_count > 0 else 5
    
    # 繪製折線圖
    ax = plt.gca()
    sns.lineplot(x=range(len(daily_counts)), y=daily_counts.values, marker='o', markersize=10, 
                linewidth=2, color='#1f77b4')
    
    # 設定圖表樣式
    plt.title('感測器滿載次數統計', fontproperties=font, fontsize=14, pad=20)
    plt.xlabel('日期', fontproperties=font, fontsize=12)
    plt.ylabel('滿載次數', fontproperties=font, fontsize=12)
    
    # 設定y軸範圍和間隔
    plt.ylim(0, y_max)
    plt.yticks(range(int(y_max) + 1))
    
    # 設定x軸標籤
    date_labels = [d.strftime('%m/%d') for d in daily_counts.index]
    plt.xticks(range(len(daily_counts)), date_labels, rotation=45)
    
    # 在每個點上標註數值
    for i, v in enumerate(daily_counts.values):
        plt.text(i, v + 0.1, str(int(v)), ha='center', va='bottom', fontsize=10)
    
    # 加入格線
    plt.grid(True, linestyle='--', alpha=0.3)
    
    # 調整布局
    plt.tight_layout()
    
    # 保存圖表
    plt.savefig('static/images/weekly_sensor_data.png', dpi=300, bbox_inches='tight')
    plt.close()

@app.route('/')
def index():
    # 獲取感測器數據
    sensor_data = get_sensor_data()
    
    # 分析數據並生成圖表
    analyze_weekly_sensor_data(sensor_data)
    
    # 渲染網頁模板
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)