import pyodbc
import pandas as pd
import json
import os


def load_config():
    """Hàm đọc file config.json cùng thư mục"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'config.json')

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ==========================================
# 1. KẾT NỐI & XÁC THỰC
# ==========================================
def connect_db():
    """Tạo kết nối đến SQL Server dựa trên file config.json"""
    try:
        # Đọc thông số từ file JSON
        config = load_config()
        server = config.get("server")
        database = config.get("database")
        trusted = "yes" if config.get("trusted_connection") else "no"

        # Lắp ráp chuỗi kết nối
        conn_str = (
            r'DRIVER={ODBC Driver 17 for SQL Server};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'Trusted_Connection={trusted};'
            r'TrustServerCertificate=yes;'
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"❌ Lỗi kết nối CSDL: {e}")
        return None


def check_login(username, password):
    """Kiểm tra tài khoản trong bảng Employees. Trả về True/False"""
    pass


# ==========================================
# 2. CRUD: QUẢN LÝ NHÂN VIÊN
# ==========================================
def get_all_employees():
    pass


def create_employee(username, password, fullname, role):
    pass


def update_employee(employee_id, fullname, role, is_active):
    pass


# ==========================================
# 3. CRUD: DANH MỤC & MẪU SẢN PHẨM
# ==========================================
def get_all_categories():
    pass


def get_all_product_models():
    pass


def create_product_model(model_code, model_name, category_id, base_price):
    pass


# ==========================================
# 4. CRUD: KHO & BIẾN THỂ (VARIANTS)
# ==========================================
def get_inventory():
    """Lấy danh sách tồn kho hiện tại"""
    pass


def create_product_variant(model_id, color, size, current_stock):
    pass


def update_stock(variant_id, stock_added):
    """Cộng thêm số lượng khi nhập hàng"""
    pass


# ==========================================
# 5. NGHIỆP VỤ BÁN HÀNG & AI DỰ BÁO
# ==========================================
def add_internal_sales(variant_id, sale_date, quantity_sold, actual_price):
    """Ghi nhận 1 đơn hàng mới"""
    pass


def save_ai_forecast(variant_id, target_date, predicted_demand, suggested_restock):
    """Lưu số liệu do AI tính toán vào bảng AI_Forecast_Results"""
    pass


def get_dashboard_forecast_data():
    """
    (READ) Lấy Tồn kho thực tế + Dự báo AI.
    Lưu ý cho DB: Cần tính toán luôn cột [Chênh Lệch] = Tồn kho - Dự báo.
    Nếu Chênh lệch < 0 -> Báo động đỏ cho UI.
    """
    pass


def export_inventory_to_excel(file_path="Bao_Cao_Ton_Kho.xlsx"):
    """
    (TÍNH NĂNG MỚI - EXCEL)
    Hàm này sẽ chạy lệnh SQL Lấy toàn bộ dữ liệu Tồn kho + Dự báo,
    sau đó dùng pandas.DataFrame.to_excel() để lưu thẳng ra máy tính.
    """
    pass


# ==========================================
# TEST NHANH KẾT NỐI (Chạy khi gõ: python db_manager.py)
# ==========================================
if __name__ == "__main__":
    print("--- KIỂM TRA ĐƯỜNG ỐNG DỮ LIỆU BẰNG CONFIG.JSON ---")
    conn = connect_db()
    if conn:
        print("✅ KẾT NỐI THÀNH CÔNG! Đã nạp cấu hình từ config.json")
        conn.close()
    else:
        print("⚠️ Hãy kiểm tra lại file config.json của anh nhé!")