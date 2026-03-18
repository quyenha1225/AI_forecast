import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# --- FIX ĐƯỜNG DẪN BÁ ĐẠO ---
path_finder = os.path.abspath(__file__)
while os.path.basename(path_finder) != 'src' and path_finder != os.path.dirname(path_finder):
    path_finder = os.path.dirname(path_finder)
project_root = os.path.dirname(path_finder)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import Component Giao diện từ file Sếp vừa tạo
try:
    from src.frontend.components import apply_custom_css, render_metric_card
except ModuleNotFoundError:
    st.error("❌ Không tìm thấy file components.py trong src/frontend")
    st.stop()

try:
    from src.controllers.main_controller import MainController
except ModuleNotFoundError:
    st.error(f"❌ Không tìm thấy thư mục 'src'. Vui lòng kiểm tra lại cấu trúc.")
    st.stop()

# ==========================================
# CẤU HÌNH & KHỞI TẠO
# ==========================================
st.set_page_config(page_title="Retail AI Enterprise", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")
apply_custom_css()  # 🚀 Gọi hàm nhúng CSS từ file components.py

if 'controller' not in st.session_state:
    with st.spinner("🧠 Đang khởi động não bộ AI..."):
        st.session_state.controller = MainController()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.session_state.ai_results = None


@st.cache_data(ttl=60)
def get_fast_inventory():
    return st.session_state.controller.get_inventory_view()


@st.cache_data(ttl=60)
def get_fast_sku_list():
    return pd.DataFrame(st.session_state.controller.get_full_inventory_list_for_dropdown())


def get_cached_dashboard_data():
    if 'dash_data' not in st.session_state or time.time() - st.session_state.get('dash_time', 0) > 60:
        ctrl = st.session_state.controller

        # Nhận thêm biến df_can_nhap để hiển thị danh sách đỏ
        tong_ton, tong_du_bao, thieu_hang, df_can_nhap = ctrl.get_dashboard_metrics()
        df_trend = ctrl.get_trend_chart_data()
        df_market = ctrl.get_market_chart_data()
        df_category = pd.DataFrame(ctrl.get_category_structure_data())

        st.session_state.dash_data = (tong_ton, tong_du_bao, thieu_hang, df_can_nhap, df_trend, df_market, df_category)
        st.session_state.dash_time = time.time()
    return st.session_state.dash_data


def clear_cache():
    if 'dash_data' in st.session_state: del st.session_state.dash_data
    get_fast_inventory.clear()
    get_fast_sku_list.clear()


def logout():
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.session_state.ai_results = None
    clear_cache()
    st.rerun()


# ==========================================
# CÁC MÀN HÌNH CHÍNH
# ==========================================
def show_login_page():
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(
            "<div class='login-container'><div style='font-size: 3rem; margin-bottom: 10px;'>🛡️</div><h1 style='color: white; margin-bottom: 5px; font-weight: 800;'>HỆ THỐNG QUẢN TRỊ</h1><p style='color: #94A3B8; margin-bottom: 25px; font-weight: 500;'>Fashion AI Market - Enterprise Edition</p>",
            unsafe_allow_html=True)
        with st.form("login_form"):
            user = st.text_input("👤 Tên Đăng Nhập")
            pw = st.text_input("🔑 Mật Khẩu", type="password")
            if st.form_submit_button("🚀 KÍCH HOẠT ĐĂNG NHẬP", use_container_width=True):
                res = st.session_state.controller.handle_login(user, pw)
                if res:
                    st.session_state.logged_in = True
                    st.session_state.user_data = res
                    st.rerun()
                else:
                    st.error("❌ Sai tài khoản hoặc mật khẩu!")
        st.markdown("</div>", unsafe_allow_html=True)


def show_dashboard():
    st.title("🛍️ Dashboard Tổng Quan & Phân Tích AI")
    # Giải nén đầy đủ các biến, kể cả df_can_nhap
    tong_ton, tong_du_bao, thieu_hang, df_can_nhap, df_trend, df_market, df_category = get_cached_dashboard_data()

    m1, m2, m3 = st.columns(3)
    # 🚀 Gọi hàm vẽ thẻ từ file components
    with m1:
        render_metric_card("Tổng Tồn Kho", f"{tong_ton:,.0f}", "Sản phẩm thực tế", "🏭")
    with m2:
        render_metric_card("Mã Cần Nhập Gấp", f"{thieu_hang}", "Nguy cơ đứt gãy", "🚨", "#EF4444")
    with m3:
        render_metric_card("Dự Báo Cầu AI", f"{tong_du_bao:,.0f}", "Nhu cầu thị trường", "🧠", "#10B981")

    # 🚀 TÍNH NĂNG MỚI: Bấm để xem danh sách nhập gấp
    if thieu_hang > 0:
        with st.expander(f"🚨 BẤM VÀO ĐÂY ĐỂ XEM DANH SÁCH {thieu_hang} MÃ CẦN NHẬP GẤP TRONG THÁNG NÀY"):
            st.dataframe(df_can_nhap.style.highlight_max(subset=['Cần Nhập Thêm'], color='rgba(239, 68, 68, 0.4)'),
                         use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📈 Xu hướng Bán hàng", "⚔️ Cạnh tranh Giá", "🍩 Cơ cấu Danh mục"])

    with t1:
        if not df_trend.empty:
            df_trend = df_trend.iloc[::-1]
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=df_trend['Ngay'], y=df_trend['ThucBan'], name='Thực Bán', mode='lines+markers',
                                      line=dict(color='#10B981', width=3), fill='tozeroy',
                                      fillcolor='rgba(16, 185, 129, 0.2)'))
            fig1.add_trace(go.Scatter(x=df_trend['Ngay'], y=df_trend['AIDuBao'], name='AI Dự Báo', mode='lines+markers',
                                      line=dict(color='#3B82F6', width=3, dash='dot')))
            fig1.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               hovermode='x unified')
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu xu hướng.")

    with t2:
        if not df_market.empty:
            fig2 = go.Figure(data=[
                go.Bar(name='Giá Mình Bán', x=df_market['ModelName'], y=df_market['GiaCuaMinh'],
                       marker_color='#3B82F6'),
                go.Bar(name='Giá Đối Thủ', x=df_market['ModelName'], y=df_market['GiaDoiThu'], marker_color='#EF4444')
            ])
            fig2.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               barmode='group')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu giá đối thủ.")

    with t3:
        if not df_category.empty and 'TongTonKho' in df_category.columns:
            fig3 = px.pie(df_category, values='TongTonKho', names='CategoryName', hole=0.5,
                          color_discrete_sequence=px.colors.sequential.Plasma)
            fig3.update_traces(textposition='inside', textinfo='percent+label')
            fig3.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu cơ cấu danh mục.")


def show_inventory():
    st.title("📦 Quản Lý Kho Thực Tế (Inventory)")
    df_inv = get_fast_inventory()
    if not df_inv.empty:
        st.dataframe(df_inv.head(1000), use_container_width=True, height=450)
        csv = df_inv.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Xuất Toàn Bộ File Kiểm Kho (.csv)", data=csv, file_name='Kiem_Kho_Full.csv',
                           mime='text/csv')
    else:
        st.warning("⚠️ Kho hàng hiện đang trống!")


def show_data_entry():
    st.title("📥 Trạm Cập Nhật Dữ Liệu Thực Tế")
    ctrl = st.session_state.controller
    df_sku = get_fast_sku_list()
    if not df_sku.empty:
        with st.form("update_stock_form"):
            sku_dict = dict(zip(df_sku['SKU_Name'], df_sku['VariantID']))
            selected_sku_name = st.selectbox("Chọn Mã Sản Phẩm", list(sku_dict.keys()))
            col1, col2 = st.columns(2)
            with col1:
                loai = st.radio("Loại giao dịch", ["➕ Nhập kho", "➖ Xuất bán"], horizontal=True)
            with col2:
                qty = st.number_input("Số lượng", min_value=1, value=10)

            if st.form_submit_button("💾 XÁC NHẬN CẬP NHẬT VÀO SQL", type="primary"):
                success = ctrl.update_stock_transaction(sku_dict[selected_sku_name], qty, "Nhập kho" in loai)
                if success:
                    st.success("✅ Cập nhật Database thành công!")
                    clear_cache()
                    st.balloons()
                else:
                    st.error("❌ Xảy ra lỗi khi cập nhật!")


def show_ai_config():
    st.title("🤖 Trung Tâm Điều Khiển AI")
    st.markdown("### ⚙️ Thông số đầu vào cho Lõi AI (CNN & Ensemble)")
    ctrl = st.session_state.controller

    col1, col2 = st.columns(2)
    with col1:
        cat_list = [c['CategoryName'] for c in ctrl.get_categories()] if ctrl.get_categories() else ["Chưa có dữ liệu"]
        danh_muc = st.selectbox("Chọn Danh Mục cần Dự báo", cat_list)
        hot_trend = st.slider("Độ Hot Trend (Market Score)", 1, 10, 8)
    with col2:
        nhiet_do = st.slider("Nhiệt độ môi trường (°C)", 5, 45, 22)
        bien_dong_gia = st.number_input("Biến động giá Đối thủ (%)", value=-5.0)

    if st.button("🔥 KÍCH HOẠT HỆ THỐNG PHÂN TÍCH", type="primary", use_container_width=True):
        with st.spinner("Đang kích hoạt AI Dự báo theo tháng..."):
            time.sleep(1)
            df_real = ctrl.run_real_ai_forecast(danh_muc, hot_trend, nhiet_do, bien_dong_gia)

            if not df_real.empty:
                st.session_state.ai_results = df_real
                st.markdown("<h3 style='color: #10B981;'>🎯 KẾT QUẢ AI DỰ BÁO (TỪ DATA THẬT)</h3>",
                            unsafe_allow_html=True)
                st.dataframe(df_real.style.highlight_max(subset=['Gợi Ý Nhập Thêm'], color='rgba(239, 68, 68, 0.3)'),
                             use_container_width=True)

    if st.session_state.ai_results is not None:
        if st.button("💾 Phê duyệt & Lưu SQL", type="primary", use_container_width=True):
            if ctrl.save_predictions(st.session_state.ai_results):
                st.toast("Đã lưu kết quả dự báo AI thành công!", icon="🎉")
                clear_cache()
                st.session_state.ai_results = None
                time.sleep(1)
                st.rerun()


def main():
    if not st.session_state.logged_in:
        show_login_page()
    else:
        with st.sidebar:
            st.markdown(
                f"<div style='text-align: center; margin-bottom: 20px;'><h2 style='color: #F8FAFC; margin-bottom: 0;'>👨‍💼 {st.session_state.user_data['FullName']}</h2><p style='color: #3B82F6; font-weight: 600;'>{st.session_state.user_data['Role']} System</p></div>",
                unsafe_allow_html=True)
            st.markdown("<hr style='border-color: #334155; margin-top: 0;'>", unsafe_allow_html=True)
            menu = st.radio("ĐIỀU HƯỚNG", ["📊 Dashboard", "📦 Inventory", "📥 Cập nhật", "🤖 AI Config"],
                            label_visibility="collapsed")
            st.markdown(
                "<br><div style='background: rgba(59, 130, 246, 0.1); border: 1px solid #3B82F6; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 15px;'><div style='font-size: 24px;'>🧠</div><div style='font-weight: 700; color: #F8FAFC; margin-top: 5px;'>CNN Active</div><div style='font-size: 0.8rem; color: #94A3B8;'>Tốc độ Load: < 0.1s</div></div><hr style='border-color: #334155;'>",
                unsafe_allow_html=True)
            if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): logout()

        if menu == "📊 Dashboard":
            show_dashboard()
        elif menu == "📦 Inventory":
            show_inventory()
        elif menu == "📥 Cập nhật":
            show_data_entry()
        elif menu == "🤖 AI Config":
            show_ai_config()


if __name__ == "__main__":
    main()