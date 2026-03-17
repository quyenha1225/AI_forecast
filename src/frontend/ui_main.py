import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# Cấu hình trang mặc định (Streamlit tự động áp dụng Dark Mode theo hệ thống)
st.set_page_config(page_title="Inventory Dashboard", layout="wide")

# --- Dữ liệu mẫu ---
@st.cache_data
def load_data():
    return pd.DataFrame({
        'ID': [1, 2, 3, 4, 5, 6],
        'Sản phẩm': ['Sản phẩm A', 'Sản phẩm B', 'Sản phẩm C', 'Sản phẩm D', 'Sản phẩm E', 'Sản phẩm F'],
        'Tồn kho': [150, 80, 200, 45, 300, 110],
        'Dự báo': [120, 100, 180, 60, 250, 150]
    })

# --- Khởi tạo Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

# --- Logic Đăng nhập ---
def login():
    st.title("Đăng nhập Hệ thống")
    st.markdown("*(Tài khoản thử nghiệm: **admin/admin** hoặc **staff/staff**)*")
    
    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập")
        
        if submitted:
            if username == "admin" and password == "admin":
                st.session_state.logged_in = True
                st.session_state.role = "Admin"
                st.session_state.username = username
                st.rerun()
            elif username == "staff" and password == "staff":
                st.session_state.logged_in = True
                st.session_state.role = "Staff"
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Tài khoản hoặc mật khẩu không hợp lệ!")

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.rerun()

# --- Giao diện chính (Dashboard) ---
if not st.session_state.logged_in:
    login()
else:
    # 1. Thanh Menu điều hướng bên trái (Sidebar)
    st.sidebar.title("Menu Điều Hướng")
    st.sidebar.write(f"👤 Xin chào, **{st.session_state.username}**")
    st.sidebar.markdown(f"Trạng thái: `{st.session_state.role}`")
    st.sidebar.button("Đăng xuất", on_click=logout)
    
    st.sidebar.divider()
    
    # Phân quyền UI trên Sidebar
    menu_options = ["Tổng quan Dashboard"]
    if st.session_state.role == "Admin":
        menu_options.append("Cài đặt")
        
    choice = st.sidebar.radio("Chọn trang:", menu_options)

    # --- TRANG TỔNG QUAN ---
    if choice == "Tổng quan Dashboard":
        st.title("📦 Quản lý Tồn kho & Dự báo")
        
        df = load_data()

        # Phân quyền UI: Nút Chạy AI chỉ hiện cho Admin
        if st.session_state.role == "Admin":
            if st.button("🚀 Chạy AI Dự báo"):
                st.success("Đang chạy mô hình AI... (Mô phỏng)")
        
        st.divider()

        # 2. Nhúng Biểu đồ Matplotlib
        st.subheader("📊 Biểu đồ So sánh Tồn kho vs Dự báo")
        
        # Thiết lập style cho biểu đồ hợp với Dark Mode của Streamlit
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 4))
        
        x = range(len(df))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], df['Tồn kho'], width, label='Tồn kho', color='#4ade80')
        ax.bar([i + width/2 for i in x], df['Dự báo'], width, label='Dự báo', color='#60a5fa')
        
        ax.set_xticks(x)
        ax.set_xticklabels(df['Sản phẩm'])
        ax.legend()
        
        # Xóa viền biểu đồ cho đẹp hơn
        for spine in ax.spines.values():
            spine.set_visible(False)
            
        st.pyplot(fig)

        st.divider()

        # 3. Bảng dữ liệu & Cảnh báo Đỏ (Pandas Styler)
        st.subheader("📋 Bảng Dữ liệu Chi tiết")
        st.markdown("*(Các dòng có Tồn kho < Dự báo được bôi đỏ)*")
        
        def highlight_warning(row):
            # Nếu Tồn kho < Dự báo, đổi màu chữ thành đỏ (Red)
            if row['Tồn kho'] < row['Dự báo']:
                return ['color: #ff4b4b; font-weight: bold'] * len(row)
            return [''] * len(row)

        styled_df = df.style.apply(highlight_warning, axis=1)
        st.dataframe(styled_df, use_container_width=True)

        # 4. Nút Tải Báo cáo Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Bao_cao')
        
        st.download_button(
            label="📥 Tải Báo cáo Excel",
            data=buffer.getvalue(),
            file_name="Bao_cao_Ton_kho.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # --- TRANG CÀI ĐẶT (Chỉ Admin) ---
    elif choice == "Cài đặt":
        st.title("⚙️ Cài đặt Hệ thống")
        st.info("Trang này chỉ hiển thị cho tài khoản Admin.")
        st.write("Các cấu hình hệ thống sẽ được đặt ở đây...")