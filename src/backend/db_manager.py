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
        config = load_config()
        server = config.get("server")
        database = config.get("database")
        trusted = "yes" if config.get("trusted_connection") else "no"

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
    """Kiểm tra tài khoản trong bảng Employees. Trả về thông tin User nếu đúng, ngược lại False"""
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "SELECT EmployeeID, FullName, Role FROM Employees WHERE Username = ? AND PasswordHash = ? AND IsActive = 1"
        cursor.execute(query, (username, password))
        row = cursor.fetchone()
        if row:
            return {"EmployeeID": row[0], "FullName": row[1], "Role": row[2]}
        return False
    except Exception as e:
        print(f"❌ Lỗi check_login: {e}")
        return False
    finally:
        conn.close()


# ==========================================
# 2. CRUD: QUẢN LÝ NHÂN VIÊN
# ==========================================
def get_all_employees():
    conn = connect_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT EmployeeID, Username, FullName, Role, IsActive FROM Employees")
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def create_employee(username, password, fullname, role):
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO Employees (Username, PasswordHash, FullName, Role) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (username, password, fullname, role))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Lỗi create_employee: {e}")
        return False
    finally:
        conn.close()


def update_employee(employee_id, fullname, role, is_active):
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "UPDATE Employees SET FullName=?, Role=?, IsActive=? WHERE EmployeeID=?"
        cursor.execute(query, (fullname, role, is_active, employee_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Lỗi update_employee: {e}")
        return False
    finally:
        conn.close()


# ==========================================
# 3. CRUD: DANH MỤC & MẪU SẢN PHẨM
# ==========================================
def get_all_categories():
    conn = connect_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT CategoryID, CategoryName FROM Categories")
        return [{"CategoryID": row[0], "CategoryName": row[1]} for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_product_models():
    conn = connect_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        query = """
        SELECT m.ModelID, m.ModelCode, m.ModelName, c.CategoryName, m.BasePrice
        FROM Product_Models m
        JOIN Categories c ON m.CategoryID = c.CategoryID
        """
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def create_product_model(model_code, model_name, category_id, base_price):
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO Product_Models (ModelCode, ModelName, CategoryID, BasePrice) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (model_code, model_name, category_id, base_price))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Lỗi create_product_model: {e}")
        return False
    finally:
        conn.close()


# ==========================================
# 4. CRUD: KHO & BIẾN THỂ (VARIANTS)
# ==========================================
def get_inventory():
    """Lấy danh sách tồn kho hiện tại"""
    conn = connect_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        query = """
        SELECT v.VariantID, m.ModelCode, m.ModelName, v.Color, v.Size, v.CurrentStock
        FROM Product_Variants v
        JOIN Product_Models m ON v.ModelID = m.ModelID
        """
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def create_product_variant(model_id, color, size, current_stock):
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO Product_Variants (ModelID, Color, Size, CurrentStock) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (model_id, color, size, current_stock))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Lỗi create_product_variant: {e}")
        return False
    finally:
        conn.close()


def update_stock(variant_id, stock_added):
    """Cộng thêm số lượng khi nhập hàng"""
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "UPDATE Product_Variants SET CurrentStock = CurrentStock + ? WHERE VariantID = ?"
        cursor.execute(query, (stock_added, variant_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Lỗi update_stock: {e}")
        return False
    finally:
        conn.close()


# ==========================================
# 5. NGHIỆP VỤ BÁN HÀNG & AI DỰ BÁO
# ==========================================
def add_internal_sales(variant_id, sale_date, quantity_sold, actual_price):
    """Ghi nhận 1 đơn hàng mới và trừ tồn kho"""
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        # Lệnh 1: Ghi nhận doanh thu
        query_sale = "INSERT INTO Internal_Sales (VariantID, SaleDate, QuantitySold, ActualSellingPrice) VALUES (?, ?, ?, ?)"
        cursor.execute(query_sale, (variant_id, sale_date, quantity_sold, actual_price))

        # Lệnh 2: Trừ tồn kho
        query_stock = "UPDATE Product_Variants SET CurrentStock = CurrentStock - ? WHERE VariantID = ?"
        cursor.execute(query_stock, (quantity_sold, variant_id))

        conn.commit()  # Nếu cả 2 lệnh thành công thì mới lưu
        return True
    except Exception as e:
        conn.rollback()  # <--- THÊM DÒNG NÀY: Hủy toàn bộ nếu có bất kỳ lệnh nào tạch
        print(f"❌ Lỗi add_internal_sales: {e}")
        return False
    finally:
        conn.close()

def save_ai_forecast(variant_id, target_date, predicted_demand, suggested_restock, suggested_price):
    """Lưu số liệu do AI tính toán vào bảng AI_Forecast_Results"""
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO AI_Forecast_Results (VariantID, TargetDate, PredictedMarketDemand, SuggestedRestock, SuggestedPrice) 
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (variant_id, target_date, predicted_demand, suggested_restock, suggested_price))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Lỗi save_ai_forecast: {e}")
        return False
    finally:
        conn.close()


def get_dashboard_forecast_data():
    """
    (READ) Lấy Tồn kho thực tế + Dự báo AI.
    Sử dụng JOIN gộp bảng Tồn Kho và Dự Báo mới nhất. Tính cột ChenhLech.
    Nếu ChenhLech < 0 -> Báo động đỏ cho UI.
    """
    conn = connect_db()
    if not conn: return []
    try:
        cursor = conn.cursor()
        query = """
        SELECT 
            v.VariantID, 
            m.ModelCode, 
            m.ModelName, 
            v.Color, 
            v.Size, 
            v.CurrentStock AS TonKho,
            ISNULL(f.PredictedMarketDemand, 0) AS DuBaoAI,
            (v.CurrentStock - ISNULL(f.PredictedMarketDemand, 0)) AS ChenhLech
        FROM Product_Variants v
        INNER JOIN Product_Models m ON v.ModelID = m.ModelID
        LEFT JOIN (
            -- Lấy kết quả dự báo mới nhất cho từng Variant
            SELECT VariantID, PredictedMarketDemand
            FROM AI_Forecast_Results
            WHERE ForecastID IN (
                SELECT MAX(ForecastID) FROM AI_Forecast_Results GROUP BY VariantID
            )
        ) f ON v.VariantID = f.VariantID
        """
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def export_inventory_to_excel(file_path="Bao_Cao_Ton_Kho.xlsx"):
    """
    (TÍNH NĂNG MỚI - EXCEL)
    Rút dữ liệu từ SQL và dùng Pandas tải file báo cáo về máy.
    """
    conn = connect_db()
    if not conn:
        print("❌ Không thể kết nối DB để xuất Excel.")
        return False

    try:
        query = """
        SELECT 
            m.ModelCode AS [Mã SP], 
            m.ModelName AS [Tên Sản Phẩm], 
            v.Color AS [Màu Sắc], 
            v.Size AS [Kích Cỡ], 
            v.CurrentStock AS [Tồn Kho Thực Tế],
            ISNULL(f.PredictedMarketDemand, 0) AS [AI Dự Báo Bán Ra],
            (v.CurrentStock - ISNULL(f.PredictedMarketDemand, 0)) AS [Chênh Lệch (Tồn - Dự báo)]
        FROM Product_Variants v
        INNER JOIN Product_Models m ON v.ModelID = m.ModelID
        LEFT JOIN (
            SELECT VariantID, PredictedMarketDemand
            FROM AI_Forecast_Results
            WHERE ForecastID IN (SELECT MAX(ForecastID) FROM AI_Forecast_Results GROUP BY VariantID)
        ) f ON v.VariantID = f.VariantID
        ORDER BY [Chênh Lệch (Tồn - Dự báo)] ASC
        """

        # Dùng Pandas đọc trực tiếp từ SQL Query
        df = pd.read_sql(query, conn)

        # Xuất ra file Excel
        df.to_excel(file_path, index=False, engine='openpyxl')
        print(f"✅ Đã xuất báo cáo Excel thành công tại: {file_path}")
        return True

    except Exception as e:
        print(f"❌ Lỗi khi xuất Excel: {e}")
        return False
    finally:
        conn.close()


# ==========================================
# TEST NHANH KẾT NỐI (Chạy khi gõ: python db_manager.py)
# ==========================================
if __name__ == "__main__":
    print("--- KIỂM TRA ĐƯỜNG ỐNG DỮ LIỆU BẰNG CONFIG.JSON ---")
    conn = connect_db()
    if conn:
        print("✅ KẾT NỐI THÀNH CÔNG! Đã nạp cấu hình từ config.json")
        conn.close()

        # Test thử hàm lấy dữ liệu Dashboard và xuất Excel
        print("\n--- TEST DỮ LIỆU DASHBOARD ---")
        dashboard_data = get_dashboard_forecast_data()
        print(f"Tìm thấy {len(dashboard_data)} bản ghi.")

        print("\n--- TEST XUẤT EXCEL ---")
        export_inventory_to_excel("Test_Bao_Cao.xlsx")
    else:
        print("⚠️ Hãy kiểm tra lại file config.json của anh nhé!")