import streamlit as st

def apply_custom_css():
    """Hàm chứa toàn bộ CSS Cyberpunk của hệ thống"""
    theme_css = """
    :root { --card-bg: #1E293B; --text-main: #F8FAFC; --text-muted: #94A3B8; --border-color: #334155; --hover-bg: rgba(255, 255, 255, 0.05); --primary-glow: rgba(59, 130, 246, 0.5); }
    .block-container { padding-top: 4rem; padding-bottom: 2rem; }
    div[data-testid="stRadio"] > div { gap: 12px; }
    div[data-testid="stRadio"] label[data-baseweb="radio"] { background: rgba(30, 41, 59, 0.5); padding: 12px 20px; border-radius: 12px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); border: 1px solid var(--border-color); width: 100%; cursor: pointer; }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover { background: var(--hover-bg); transform: translateX(8px); border-color: #3B82F6; box-shadow: 0 4px 15px var(--primary-glow); }
    div[data-testid="stRadio"] label[data-baseweb="radio"] p { font-size: 1.1rem; font-weight: 600; margin: 0; color: #E2E8F0; }
    .login-container { background: var(--card-bg); padding: 40px; border-radius: 20px; border: 1px solid #334155; box-shadow: 0 0 30px rgba(59, 130, 246, 0.15); text-align: center; margin-top: 50px; }
    .metric-card { background-color: var(--card-bg); border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); color: var(--text-main); transition: all 0.3s ease-in-out; border: 1px solid var(--border-color); border-top: 4px solid #3B82F6; position: relative; overflow: hidden; }
    .metric-card:hover { transform: translateY(-8px); box-shadow: 0 15px 25px -5px var(--primary-glow); border-color: #3B82F6; }
    .metric-title { font-size: 1rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px; }
    .metric-value { font-size: 2.5rem; font-weight: 800; margin-bottom: 8px; color: #FFFFFF; }
    .metric-icon { font-size: 2.5rem; position: absolute; top: 20px; right: 20px; opacity: 0.2; transition: 0.3s; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 2px solid var(--border-color); }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: transparent; border-radius: 8px 8px 0px 0px; padding: 10px 20px; font-weight: 600; color: var(--text-muted); }
    .stTabs [aria-selected="true"] { color: #3B82F6 !important; border-bottom: 3px solid #3B82F6 !important; background: rgba(59, 130, 246, 0.05); }
    [data-testid="stExpander"] details summary { background-color: rgba(239, 68, 68, 0.1); border-radius: 8px; border: 1px solid #EF4444; color: #EF4444; font-weight: bold;}
    """
    st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)

def render_metric_card(title, value, sub_text, icon="📦", border_color="#3B82F6"):
    """Hàm vẽ các thẻ (Nút) thống kê to đùng trên Dashboard"""
    st.markdown(f"""
    <div class="metric-card" style="border-top-color: {border_color};">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div style="color: var(--text-muted); font-size: 0.85rem; font-weight: 500;">{sub_text}</div>
        <div class="metric-icon">{icon}</div>
    </div>
    """, unsafe_allow_html=True)