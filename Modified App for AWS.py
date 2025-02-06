import json
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from matplotlib.font_manager import FontProperties
import boto3
import os
from jinja2 import Environment, FileSystemLoader

# AWS S3 配置
S3_BUCKET = 'your-bucket-name'  # 請替換為你的 S3 bucket 名稱
AWS_REGION = 'ap-northeast-1'   # 請替換為你的 AWS region

def upload_to_s3(local_path, s3_path, content_type=None):
    """上傳檔案到 S3"""
    s3_client = boto3.client('s3')
    extra_args = {}
    if content_type:
        extra_args['ContentType'] = content_type
    try:
        s3_client.upload_file(local_path, S3_BUCKET, s3_path, ExtraArgs=extra_args)
        print(f"Successfully uploaded {local_path} to s3://{S3_BUCKET}/{s3_path}")
    except Exception as e:
        print(f"Error uploading to S3: {e}")

def get_sensor_data():
    # [原有的 get_sensor_data 函數保持不變]
    with open('sql.json', 'r') as file:
        db_config = json.load(file)
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = """
        SELECT identify_time, results 
        FROM sensor 
        ORDER BY identify_time DESC
        LIMIT 100
        """
        cursor.execute(query)
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=['identify_time', 'results'])
        return df
    except Exception as e:
        print(f"發生錯誤: {e}")
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def analyze_weekly_sensor_data(df):
    # [原有的 analyze_weekly_sensor_data 函數保持不變，但修改儲存路徑]
    if df is None or df.empty:
        print("沒有資料可供分析")
        return None
        
    font = FontProperties(fname='SimHei.ttf')
    df['identify_time'] = pd.to_datetime(df['identify_time'])
    df['date'] = df['identify_time'].dt.date
    daily_counts = df[df['results'] == '滿'].groupby('date').size()
    daily_counts = daily_counts.sort_index(ascending=False).head(7)
    daily_counts = daily_counts.sort_index()
    
    plt.figure(figsize=(12, 6))
    max_count = daily_counts.max()
    y_max = max_count + 1 if max_count > 0 else 5
    
    ax = plt.gca()
    sns.lineplot(x=range(len(daily_counts)), y=daily_counts.values, marker='o', 
                markersize=10, linewidth=2, color='#1f77b4')
    
    plt.title('感測器滿載次數統計', fontproperties=font, fontsize=14, pad=20)
    plt.xlabel('日期', fontproperties=font, fontsize=12)
    plt.ylabel('滿載次數', fontproperties=font, fontsize=12)
    
    plt.ylim(0, y_max)
    plt.yticks(range(int(y_max) + 1))
    
    date_labels = [d.strftime('%m/%d') for d in daily_counts.index]
    plt.xticks(range(len(daily_counts)), date_labels, rotation=45)
    
    for i, v in enumerate(daily_counts.values):
        plt.text(i, v + 0.1, str(int(v)), ha='center', va='bottom', fontsize=10)
    
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    
    # 修改儲存路徑
    plt.savefig('weekly_sensor_data.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return date_labels, daily_counts.values.tolist()

def generate_static_site():
    """生成靜態網站內容"""
    # 獲取資料並生成圖表
    sensor_data = get_sensor_data()
    dates, counts = analyze_weekly_sensor_data(sensor_data)
    
    # 使用 Jinja2 渲染模板
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html')
    
    # 渲染 HTML
    html_content = template.render(
        dates=dates,
        counts=counts,
        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # 儲存檔案
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def deploy_to_s3():
    """部署檔案到 S3"""
    # 生成靜態內容
    generate_static_site()
    
    # 上傳 HTML 檔案
    upload_to_s3('index.html', 'index.html', 'text/html')
    
    # 上傳圖表
    upload_to_s3('weekly_sensor_data.png', 'weekly_sensor_data.png', 'image/png')
    
    # 上傳其他靜態資源（如果有的話）
    static_dir = 'static'
    for root, dirs, files in os.walk(static_dir):
        for file in files:
            local_path = os.path.join(root, file)
            s3_path = os.path.relpath(local_path, '.')
            upload_to_s3(local_path, s3_path)

if __name__ == "__main__":
    deploy_to_s3()