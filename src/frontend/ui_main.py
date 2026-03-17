import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import io
import pyodbc # Thư viện kết nối SQL Server

# ==========================================
# 1. CẤU HÌNH TRANG & QUẢN LÝ STATE
# ==========================================
st.set_page_config(page_title="Dashboard", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. CUSTOM CSS (UI/UX & THEME VARIABLES)
# ==========================================
# Cố định giao diện Dark Mode
theme_css = """
:root {
    --card-bg: #1E293B;
    --text-main: #F8FAFC;
    --text-muted: #94A3B8;
    --border-color: #334155;
    --hover-bg: rgba(255, 255, 255, 0.05);
    --table-header: #0F172A;
    --table-hover: #334155;
}
"""
plotly_template = "plotly_dark"

st.markdown(f"""
<style>
    {theme_css}
    
    /* Reset padding */
    .block-container {{ padding-top: 2rem; padding-bottom: 2rem; }}
    
    /* ==========================================
       STYLE CHO SIDEBAR MENU
       ========================================== */
    .stRadio div[role="radiogroup"] > label {{
        background: transparent;
        padding: 10px 15px;
        border-radius: 12px;
        margin-bottom: 8px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid transparent;
        width: 100%;
        cursor: pointer;
    }}
    .stRadio div[role="radiogroup"] > label:hover {{
        background: var(--hover-bg);
        transform: translateX(8px);
        border-color: var(--border-color);
    }}
    .stRadio div[role="radiogroup"] label p {{
        font-size: 1.05rem;
        font-weight: 500;
        margin: 0;
    }}

    /* ==========================================
       STYLE CHO AI PROMO CARD
       ========================================== */
    .ai-promo-card {{
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        border-radius: 16px;
        padding: 20px;
        color: white;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 15px;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);
        position: relative;
        overflow: hidden;
    }}
    .ai-promo-card::before {{
        content: '';
        position: absolute;
        top: -20px;
        right: -20px;
        width: 80px;
        height: 80px;
        background: rgba(255,255,255,0.2);
        border-radius: 50%;
        filter: blur(20px);
    }}
    .ai-icon {{ font-size: 24px; margin-bottom: 8px; }}
    .ai-title {{ font-weight: 600; font-size: 1rem; margin-bottom: 4px; }}
    .ai-desc {{ font-size: 0.8rem; opacity: 0.9; line-height: 1.4; }}

    /* ==========================================
       STYLE CHO METRIC CARDS & DATA TABLE
       ========================================== */
    .metric-card {{
        background-color: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        color: var(--text-main);
        transition: all 0.3s ease;
        border: 1px solid var(--border-color);
    }}
    .metric-card:hover {{
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #3B82F6;
    }}
    .metric-title {{ font-size: 0.9rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;}}
    .metric-value {{ font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;}}
    .metric-delta.up {{ color: #10B981; background: rgba(16, 185, 129, 0.1); padding: 2px 8px; border-radius: 12px; font-size: 0.85rem;}}
    .metric-delta.down {{ color: #EF4444; background: rgba(239, 68, 68, 0.1); padding: 2px 8px; border-radius: 12px; font-size: 0.85rem;}}
    
    .custom-table-container {{
        width: 100%; overflow-x: auto;
        background-color: var(--card-bg);
        border-radius: 1rem;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-top: 1rem;
    }}
    .custom-table {{ width: 100%; border-collapse: collapse; color: var(--text-main); font-family: 'Inter', sans-serif; }}
    .custom-table th {{
        background-color: var(--table-header); color: var(--text-muted);
        font-weight: 600; text-align: left; padding: 1rem;
        border-bottom: 1px solid var(--border-color); font-size: 0.85rem; text-transform: uppercase;
    }}
    .custom-table td {{ padding: 1rem; border-bottom: 1px solid var(--border-color); transition: background-color 0.2s; font-size: 0.95rem; }}
    .custom-table tr:hover td {{ background-color: var(--table-hover); }}
    
    .row-warning {{ color: #EF4444 !important; font-weight: 500; background-color: rgba(239, 68, 68, 0.05); }}
    .row-warning:hover td {{ background-color: rgba(239, 68, 68, 0.1) !important; }}
    
    .status-badge {{ padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; display: inline-block; }}
    .status-ok {{ background: rgba(16, 185, 129, 0.1); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.2); }}
    .status-warning {{ background: rgba(239, 68, 68, 0.1); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); }}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. DATABASE MODULE (PYODBC LÀM VIỆC VỚI SQL SERVER)
# ==========================================
# CỜ ĐIỀU KHIỂN: Đổi thành True khi bạn đã setup xong Database thật
USE_REAL_DB = False 

class DatabaseConfig:
    # THAY ĐỔI CÁC THÔNG SỐ NÀY KHI DÙNG DB THẬT
    SERVER = 'TEN_SERVER_CUA_BAN' # VD: 'localhost\SQLEXPRESS' hoặc '192.168.1.100'
    DATABASE = 'TEN_DATABASE'     # VD: 'RetailDB'
    USERNAME = 'SA'               # Tên đăng nhập SQL Server
    PASSWORD = 'MAT_KHAU'         # Mật khẩu SQL Server
    
    @classmethod
    def get_connection_string(cls):
        # Chuỗi kết nối chuẩn cho SQL Server thông qua ODBC Driver 17
        return f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={cls.SERVER};DATABASE={cls.DATABASE};UID={cls.USERNAME};PWD={cls.PASSWORD}"

def get_data(query: str) -> pd.DataFrame:
    """
    Hàm lấy dữ liệu. Sẽ ưu tiên lấy từ DB thật nếu USE_REAL_DB = True.
    Nếu lỗi hoặc USE_REAL_DB = False, sẽ trả về Mock Data.
    """
    if USE_REAL_DB:
        try:
            # 1. Mở kết nối tới Database
            conn = pyodbc.connect(DatabaseConfig.get_connection_string())
            
            # 2. Dùng Pandas đọc thẳng câu lệnh SQL và trả về DataFrame
            # Hàm read_sql rất tiện, nó tự động map các cột trong SQL thành cột của DataFrame
            df = pd.read_sql(query, conn)
            
            # 3. Đóng kết nối để giải phóng tài nguyên
            conn.close()
            return df
        except Exception as e:
            # Nếu có lỗi (sai pass, sai tên server...), in ra lỗi và chạy tiếp bằng Mock Data
            st.error(f"Lỗi kết nối Database: {e}")
            st.warning("Đang hiển thị dữ liệu mẫu (Mock Data) do không kết nối được DB.")

    # --- MOCK DATA (Dữ liệu giả lập khi chưa có DB) ---
    if "inventory" in query.lower():
        return pd.DataFrame({
            'Tháng': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'Tồn kho': [400, 800, 500, 600, 900, 750],
            'Dự báo': [450, 750, 550, 650, 850, 800]
        })
    elif "products" in query.lower():
        return pd.DataFrame({
            'Mã SP': ['PRD-001', 'PRD-002', 'PRD-003', 'PRD-004', 'PRD-005'],
            'Sản phẩm': ['Gold Bracelet', 'Ocean Blue Plush', 'Woman High Heel', 'Smart Watch', 'Leather Wallet'],
            'Giá': [65.0, 250.0, 100.0, 199.0, 45.0],
            'Tồn kho': [15, 45, 5, 120, 8],
            'Dự báo': [20, 30, 15, 100, 25]
        })
    return pd.DataFrame()

@st.cache_data
def convert_df_to_excel_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')


# ==========================================
# 4. UI COMPONENTS RENDERERS
# ==========================================
def render_metric_card(title, value, delta_text, is_up=True, icon="📦"):
    delta_class = "up" if is_up else "down"
    arrow = "↗" if is_up else "↘"
    html = f"""
    <div class="metric-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="metric-title">{title}</div>
            <div style="font-size: 1.5rem;">{icon}</div>
        </div>
        <div class="metric-value">{value}</div>
        <div>
            <span class="metric-delta {delta_class}">{arrow} {delta_text}</span>
            <span style="color: var(--text-muted); font-size: 0.8rem; margin-left: 8px;">so với tháng trước</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_custom_table(df):
    html = """
    <div class="custom-table-container">
        <table class="custom-table">
            <thead>
                <tr>
                    <th>Mã SP</th>
                    <th>Sản phẩm</th>
                    <th style="text-align: right;">Tồn kho</th>
                    <th style="text-align: right;">Dự báo</th>
                    <th style="text-align: right;">Đơn giá</th>
                    <th style="text-align: center;">Trạng thái</th>
                </tr>
            </thead>
            <tbody>
    """
    for _, row in df.iterrows():
        is_warning = row['Tồn kho'] < row['Dự báo']
        row_class = "row-warning" if is_warning else ""
        status_html = '<span class="status-badge status-warning">Cần nhập gấp</span>' if is_warning else '<span class="status-badge status-ok">Đủ hàng</span>'
        
        html += f"""
                <tr class="{row_class}">
                    <td>{row['Mã SP']}</td>
                    <td style="font-weight: 500;">{row['Sản phẩm']}</td>
                    <td style="text-align: right;">{row['Tồn kho']}</td>
                    <td style="text-align: right;">{row['Dự báo']}</td>
                    <td style="text-align: right;">${row['Giá']:.2f}</td>
                    <td style="text-align: center;">{status_html}</td>
                </tr>
        """
    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)


# ==========================================
# 5. MAIN APP
# ==========================================
def main():
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("## Dashboard ")
        
        st.markdown("<div style='color: var(--text-muted); font-size: 0.8rem; margin-bottom: 15px; font-weight: bold;'>MENU</div>", unsafe_allow_html=True)
        
        menu_choice = st.radio(
            "Điều hướng",
            ["📊 Dashboard", "📦 Inventory", "🛒 Orders", "📄 Reports", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Thẻ AI Promo Card
        st.markdown("""
        <div class="ai-promo-card">
            <div class="ai-icon">✨</div>
            <div class="ai-title">AI Insights</div>
            <div class="ai-desc">Hệ thống sẵn sàng phân tích dữ liệu tồn kho của bạn.</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Nút Chạy AI Dự đoán
        if st.button("🚀 Chạy AI Dự đoán", use_container_width=True, type="primary"):
            with st.spinner("AI đang xử lý thuật toán..."):
                time.sleep(2)
                st.success("Đã cập nhật dự báo mới nhất!")

    # --- ROUTING ---
    if menu_choice == "📊 Dashboard":
        show_dashboard()
    else:
        st.title(menu_choice)
        st.write("Tính năng đang được phát triển...")

def show_dashboard():
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.title("My Dashboard")
    

    with st.spinner("Đang đồng bộ dữ liệu từ Database..."):
        time.sleep(0.5)
        # Các câu query này sẽ được truyền vào hàm get_data
        # Nếu USE_REAL_DB = True, nó sẽ chạy thẳng vào SQL Server
        df_trend = get_data("SELECT * FROM inventory_trend")
        df_products = get_data("SELECT * FROM products")

    # ROW 1: METRICS
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: render_metric_card("Tổng Tồn Kho", "125.4K", "12.5%", is_up=True, icon="📦")
    with m2: render_metric_card("Cần Nhập Gấp", "89 Mã", "5.2%", is_up=False, icon="⚠️")
    with m3: render_metric_card("Dự Báo Tháng Tới", "45.2K", "8.1%", is_up=True, icon="📈")
    with m4: render_metric_card("Chênh Lệch (Delta)", "-$12.4K", "2.4%", is_up=False, icon="⚖️")

    st.markdown("<br>", unsafe_allow_html=True)

    # ROW 2: CHARTS
    c1, c2 = st.columns([2, 1])
    with c1:
        # Lấy dữ liệu từ DataFrame để biểu đồ luôn đồng bộ với Database
        months = df_trend['Tháng'].tolist()
        ton_kho = df_trend['Tồn kho'].tolist()
        du_bao = df_trend['Dự báo'].tolist()

        fig = go.Figure()

        fig.add_bar(
            x=months,
            y=ton_kho,
            name="Tồn kho",
            marker=dict(
                color="#22c55e",
                line=dict(width=0)
            ),
            text=ton_kho,
            textposition="outside"
        )

        fig.add_bar(
            x=months,
            y=du_bao,
            name="Dự báo",
            marker=dict(
                color="#ef4444",
                line=dict(width=0)
            ),
            text=du_bao,
            textposition="outside"
        )

        fig.update_layout(
            title={
                "text": "📊 Nhu cầu thị trường (Market Demand)",
                "x": 0.02,
                "font": dict(size=22)
            },
            barmode="group",
            template="plotly_dark",

            # nền
            paper_bgcolor="#0b1220",
            plot_bgcolor="#0b1220",

            # legend đẹp
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),

            # margin
            margin=dict(l=40, r=40, t=60, b=40),

            # hover đẹp
            hovermode="x unified"
        )

        # trục X
        fig.update_xaxes(
            showgrid=False,
            tickfont=dict(size=12)
        )

        # trục Y
        fig.update_yaxes(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)"
        )

        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("### 💡 Đề xuất nhập hàng")
        for _, row in df_products.head(3).iterrows():
            status_color = "#EF4444" if row['Tồn kho'] < row['Dự báo'] else "#10B981"
            st.markdown(f"""
            <div style="background: var(--card-bg); padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid var(--border-color); transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                <div style="display: flex; justify-content: space-between;">
                    <b style="color: var(--text-main);">{row['Sản phẩm']}</b>
                    <span style="color: {status_color}; font-weight: bold;">Tồn: {row['Tồn kho']}</span>
                </div>
                <div style="color: var(--text-muted); font-size: 14px; margin-top: 5px;">Giá: ${row['Giá']}</div>
            </div>
            """, unsafe_allow_html=True)

    # ROW 3: CUSTOM DATA TABLE
    st.markdown("<br><hr style='border-color: var(--border-color);'><br>", unsafe_allow_html=True)
    
    col_table_title, col_download = st.columns([4, 1])
    with col_table_title:
        st.markdown("### 📋 Chi tiết Tồn kho (Treeview Data)")
        st.caption("Cảnh báo: Các dòng có Tồn kho < Dự báo được tự động đổi màu Đỏ.")
        
    with col_download:
        excel_csv_data = convert_df_to_excel_csv(df_products)
        st.download_button(
            label="📥 Tải Báo cáo Excel",
            data=excel_csv_data,
            file_name='Bao_cao_Ton_kho.csv',
            mime='text/csv',
            use_container_width=True,
            type="primary"
        )

    render_custom_table(df_products)

if __name__ == "__main__":
    main()