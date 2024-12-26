import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile
import os
import requests
import json
from datetime import datetime
import plotly.express as px
import pandas as pd
from ast import literal_eval

# 設置頁面配置，增加側邊欄寬度
st.set_page_config(
    page_title="Blockchain Visualization",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS 來調整側邊欄寬度
st.markdown("""
    <style>
        [data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 450px;
            max-width: 450px;
        }
    </style>
""", unsafe_allow_html=True)

def fetch_blockchain_data(server_url="http://localhost:8000"):
    """從區塊鏈服務器獲取數據"""
    try:
        response = requests.get(f"{server_url}/get_chain")
        data = response.json()
        return data["chain"]
    except Exception as e:
        st.error(f"Error fetching blockchain data: {str(e)}")
        return []

def format_blockchain_data(chain_data):
    """將原始區塊鏈數據轉換為視覺化所需的格式"""
    formatted_data = []
    for block in chain_data:
        # 將時間戳轉換為易讀格式
        timestamp = block["timestamp"]
        try:
            # 假設時間戳是以秒為單位的整數
            from datetime import datetime
            formatted_time = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        except:
            # 如果轉換失敗，保持原始格式
            formatted_time = timestamp
            
        block_info = {
            "block_number": len(formatted_data) + 1,
            "hash": block["hash"],
            "prev_hash": block["previous_hash"],
            "timestamp": formatted_time,
            "difficulty": block["difficulty"],
            "miner": block["miner"],
            "transactions": block["transactions"]
        }
        formatted_data.append(block_info)
    return formatted_data

def create_blockchain_graph(data):
    """創建區塊鏈圖"""
    G = nx.DiGraph()
    
    for block in data:
        # 創建節點標籤，顯示為 "Block X" 格式
        label = f"Block {block['block_number']}"
        
        # 創建詳細的交易信息
        tx_info = ""
        if block['transactions']:
            tx_info = "Data:\n"
            for tx in block['transactions']:
                # ���理時間戳
                timestamp = tx.get('timestamp', 'N/A')
                try:
                    formatted_time = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_time = timestamp
                
                tx_info += f"From: {tx['sender']}...\n"
                tx_info += f"Time: {formatted_time}\n"
                
                try:
                    # 使用 literal_eval 來解析消息
                    message_dict = literal_eval(tx['message'])
                    for key, value in message_dict.items():
                        tx_info += f"{key}: {value}\n"
                except Exception:
                    tx_info += f"message: {tx['message']}\n"
                tx_info += "-------------------\n"
        else:
            tx_info = "No data"
        
        # 創建節點懸停信息，使用更詳細的格式
        hover_info = (
            f"Block {block['block_number']}\n"
            f"Timestamp: {block['timestamp']}\n\n"
            f"Hash:\n{block['hash']}\n\n"
            f"Previous Hash:\n{block['prev_hash']}\n\n"
            f"{tx_info}"
        )
        
        G.add_node(
            block["hash"],
            label=label,
            title=hover_info,  # PyVis���懸停文本
        )
        
        # 只在previous_hash對應的區塊存在於當前顯示範圍內時才添加邊
        if block["prev_hash"] and any(b["hash"] == block["prev_hash"] for b in data):
            G.add_edge(block["prev_hash"], block["hash"])
    
    return G

def plot_interactive_blockchain(G):
    """使用PyVis繪製互動圖"""
    net = Network(height="600px", width="100%", directed=True, bgcolor="#222222")
    
    # 配置視覺化參數
    net.set_options("""
    {
        "nodes": {
            "shape": "circle",
            "font": {
                "size": 20,
                "face": "arial",
                "color": "white",
                "bold": true
            },
            "size": 45,
            "color": {
                "background": "#2B7CE9",
                "border": "#97C2FC",
                "highlight": {
                    "background": "#00FF00",
                    "border": "#97C2FC"
                },
                "hover": {
                    "background": "#0099FF",
                    "border": "#97C2FC"
                }
            },
            "borderWidth": 2,
            "shadow": {
                "enabled": true,
                "color": "rgba(0,0,0,0.5)",
                "size": 10,
                "x": 5,
                "y": 5
            }
        },
        "edges": {
            "color": {
                "color": "#848484",
                "highlight": "#00FF00",
                "hover": "#848484"
            },
            "width": 2,
            "smooth": {
                "type": "curvedCW",
                "roundness": 0.2
            },
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.5,
                    "type": "arrow"
                }
            },
            "shadow": {
                "enabled": true,
                "color": "rgba(0,0,0,0.5)",
                "size": 10,
                "x": 5,
                "y": 5
            }
        },
        "physics": {
            "enabled": true,
            "barnesHut": {
                "gravitationalConstant": -2000,
                "centralGravity": 0.3,
                "springLength": 150,
                "springConstant": 0.04,
                "damping": 0.09,
                "avoidOverlap": 1
            },
            "solver": "barnesHut",
            "stabilization": {
                "enabled": true,
                "iterations": 1000,
                "updateInterval": 100,
                "onlyDynamicEdges": false,
                "fit": true
            }
        },
        "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": false,
            "dragNodes": true,
            "dragView": true,
            "zoomView": true
        }
    }
    """)

    # 添加節點和邊
    for node in G.nodes():
        # 獲取節點屬性，如果不存在則使用默認值
        node_data = G.nodes[node]
        label = node_data.get('label', str(node))
        title = node_data.get('title', '')
        net.add_node(node, label=label, title=title)
        
    for source, target in G.edges():
        net.add_edge(source, target)

    # 保存並顯示圖形
    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = os.path.join(tmpdir, "blockchain_graph.html")
        net.save_graph(html_path)
        with open(html_path, "r") as f:
            html_code = f.read()
        
        html_code = html_code.replace(
            '<style type="text/css">',
            '''<style type="text/css">
            html, body {
                margin: 0 !important;
                padding: 0 !important;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background-color: #222222;
            }
            #mynetwork {
                width: 100%;
                height: 100%;
                margin: 0 !important;
                padding: 0 !important;
                border: none !important;
                box-sizing: border-box;
                background-color: #222222;
            }
            .vis-network {
                outline: none !important;
                background-color: #222222;
            }
            .card {
                border-color: #222222 !important;
            }
            '''
        )
    
    # 使用固定高度顯示圖形
    st.components.v1.html(html_code, height=650, scrolling=False)

def main():
    st.title("IoT Data Blockchain Explorer")
    
    # 從服務器獲取區塊鏈數據
    blockchain_data = fetch_blockchain_data()
    if not blockchain_data:
        st.warning("No blockchain data available")
        return

    # 格式化數據
    formatted_data = format_blockchain_data(blockchain_data)
    
    # 添加視覺化控制選項
    st.sidebar.header("Control Panel")
    
    # 添加視覺化類型選擇
    visualization_type = st.sidebar.selectbox(
        "View Mode",
        ["Blockchain Network", "Sensor Data Analysis", "Pig Weight Track"]
    )
    
    # 只在 Blockchain Network 模式下顯示這些控制選項
    if visualization_type == "Blockchain Network":
        # 使用expander替換原來的header
        with st.sidebar.expander("Block Network Setting", expanded=False):
            # 添加只顯示有交易的區塊選項
            show_only_tx = st.checkbox(
                "Show only blocks with data",
                value=False
            )
            
            # 如果選擇只顯示有交易的區塊，過濾數據
            all_block_numbers = range(1, len(formatted_data) + 1)
            if show_only_tx:
                formatted_data = [block for block in formatted_data if block['transactions']]
                if not formatted_data:
                    st.warning("No blocks with data found")
                    return
                available_block_numbers = [block['block_number'] for block in formatted_data]
            else:
                available_block_numbers = list(all_block_numbers)
            
            # 修改區塊數量選擇滑動條的邏輯
            if len(formatted_data) > 1:
                num_blocks = st.slider(
                    "Number of blocks to display",
                    min_value=1,
                    max_value=len(formatted_data),
                    value=len(formatted_data)
                )
            else:
                num_blocks = 1
                st.info("Only one block available")
        
        # 使用expander替換原來的header
        with st.sidebar.expander("Block Information", expanded=False):
            # 只使用選定數量的區塊
            formatted_data = formatted_data[-num_blocks:]
            available_block_numbers = available_block_numbers[-num_blocks:]
            
            selected_block_index = st.selectbox(
                "Select Block Number",
                range(len(formatted_data)),
                format_func=lambda x: available_block_numbers[x]
            )
            
            # 顯示選中區塊的詳細信息
            selected_block = formatted_data[selected_block_index]
            st.write("### Block Details")
            st.write(f"Block Number: `{selected_block['block_number']}`")
            st.write(f"Timestamp: `{selected_block['timestamp']}`")
            st.write(f"Hash: `{selected_block['hash']}`")
            st.write(f"Previous Hash: `{selected_block['prev_hash']}`")
            
            # 顯示交易信息
            if selected_block['transactions']:
                for index, tx in enumerate(selected_block['transactions']):
                    timestamp = tx.get('timestamp', 'N/A')
                    try:
                        formatted_time = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_time = timestamp
                    
                    st.write(f"### Sensor Data {index + 1}")
                    st.write(f"- From: `{tx['sender']}`")
                    st.write(f"- Time: `{formatted_time}`")
                    
                    try:
                        # 使用 literal_eval 來解析消息
                        message_dict = literal_eval(tx['message'])
                        for key, value in message_dict.items():
                            st.write(f"-   {key}: `{value}`")
                    except Exception as e:
                        st.write(f"-   message: {tx['message']}")
    
    # 根據選擇顯示不同的視覺化內容
    if visualization_type == "Blockchain Network":
        st.subheader("Blockchain Network Visualization")
        blockchain_graph = create_blockchain_graph(formatted_data)
        plot_interactive_blockchain(blockchain_graph)
    elif visualization_type == "Sensor Data Analysis":
        st.header("Sensor Data Analysis")
        display_transaction_statistics(formatted_data)
    else:  # Pig Weight Track
        st.header("Pig Weight Tracking")
        display_pig_weight_tracking(formatted_data)
    
    # 添加自動刷新按鈕
    if st.button("Refresh Blockchain"):
        st.rerun()

# 換原來的 display_transaction_analytics 函數
def display_transaction_statistics(formatted_data):
    """顯示交易相關的統計圖表"""
    # 準備交易數據
    transactions = []
    for block in formatted_data:
        for tx in block['transactions']:
            try:
                timestamp = int(tx['timestamp'])
                formatted_time = datetime.fromtimestamp(timestamp)
                
                # 直接使用 ast.literal_eval 來安全��解析 Python 字典字串
                message_dict = literal_eval(tx['message'])
                
                # 只處理含環境感測數據的消息
                if any(key in message_dict for key in ['temperature', 'humidity', 'PM2.5']):
                    tx_data = {
                        'timestamp': formatted_time,
                        'temperature': message_dict.get('temperature'),
                        'humidity': message_dict.get('humidity'),
                        'PM2.5': message_dict.get('PM2.5')
                    }
                    transactions.append(tx_data)
            except Exception as e:
                continue

    if not transactions:
        st.warning("No sensor data available for analysis")
        return

    df = pd.DataFrame(transactions)
    
    # 創建三個時間序列圖表
    metrics = ['temperature', 'humidity', 'PM2.5']
    
    for metric in metrics:
        if metric in df.columns and not df[metric].isna().all():
            st.markdown(f"#### {metric} Monitoring")
            fig = px.line(df, x='timestamp', y=metric,
                         title=f"{metric} Time Series",
                         labels={metric: metric, 'timestamp': 'Time'})
            
            # 添加數據點標記
            fig.update_traces(
                mode='lines+markers',  # 顯示線條和數據點
                marker=dict(
                    size=8,            # 數據點大小
                    symbol='circle',   # 數據點形狀
                    line=dict(width=1) # 數據點邊框寬度
                ),
                line=dict(width=2)     # 線條寬度
            )
            
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title=metric,
                showlegend=False,
                # 添加網格線使數據更容易閱讀
                xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)'),
                yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            )
            st.plotly_chart(fig, use_container_width=True)

def display_pig_weight_tracking(formatted_data):
    """顯示豬隻體重追蹤圖表"""
    # 準備體重數據
    weight_data = []
    for block in formatted_data:
        for tx in block['transactions']:
            try:
                timestamp = int(tx['timestamp'])
                formatted_time = datetime.fromtimestamp(timestamp)
                
                # 直接使用 ast.literal_eval 來安全地解析 Python 字典字串
                message_dict = literal_eval(tx['message'])
                
                # 只處理包含豬隻ID和體重的消息
                if 'id' in message_dict and 'weight' in message_dict:
                    weight_data.append({
                        'timestamp': formatted_time,
                        'pig_id': message_dict['id'],
                        'weight': float(message_dict['weight'])
                    })
            except Exception as e:
                continue

    if not weight_data:
        st.warning("No pig weight data available for analysis")
        return

    df = pd.DataFrame(weight_data)
    
    # 獲取所有唯一的豬隻ID
    pig_ids = sorted(df['pig_id'].unique())
    
    # 添加豬隻ID選擇器
    selected_pig_ids = st.multiselect(
        "Select Pig IDs to Display",
        options=pig_ids,
        default=pig_ids[:1]  # 默認選擇第一個豬隻
    )
    
    if not selected_pig_ids:
        st.warning("Please select at least one pig to display")
        return
    
    # 過濾選定的豬隻數據
    filtered_df = df[df['pig_id'].isin(selected_pig_ids)]
    
    # 使用Plotly創建折線圖
    fig = px.line(filtered_df, 
                  x='timestamp', 
                  y='weight',
                  color='pig_id',
                  title="Pig Weight Tracking",
                  labels={'weight': 'Weight (kg)', 
                         'timestamp': 'Time',
                         'pig_id': 'Pig ID'})
    
    # 添加數據點標記
    fig.update_traces(
        mode='lines+markers',    # 顯示線條和數據點
        marker=dict(
            size=10,             # 數據點大小
            symbol='circle',     # 數據點形狀
            line=dict(width=1)   # 數據點邊框寬度
        ),
        line=dict(width=2)       # 線條寬度
    )
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Weight (kg)",
        legend_title="Pig ID",
        # 添加網格線
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 顯示統計信息
    st.markdown("#### Weight Statistics")
    stats_df = filtered_df.groupby('pig_id').agg({
        'weight': ['mean', 'min', 'max']
    }).round(2)
    stats_df.columns = ['Average Weight', 'Minimum Weight', 'Maximum Weight']
    st.dataframe(stats_df)

if __name__ == "__main__":
    main() 