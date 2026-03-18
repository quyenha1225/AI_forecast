import pyodbc
import pandas as pd
import json
import os

# ==========================================
# ⚙️ CẤU HÌNH HỆ THỐNG
# ==========================================
def load_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'config.json')
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(current_dir), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def connect_db():
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

# ==========================================
# 🔐 1. XÁC THỰC & QUẢN TRỊ NHÂN VIÊN
# ==========================================
def check_login(username, password):
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
    finally:
        conn.close()

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

# ==========================================
# 🏷️ 2. DANH MỤC & MẪU SẢN PHẨM
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
        query = """
        SELECT m.ModelID, m.ModelCode, m.ModelName, c.CategoryName, m.BasePrice
        FROM Product_Models m
        JOIN Categories c ON m.CategoryID = c.CategoryID
        """
        df = pd.read_sql(query, conn)
        return df.to_dict('records')
    finally:
        conn.close()

# ==========================================
# 📦 3. QUẢN LÝ KHO & BIẾN THỂ (ĐÃ FIX BCNF)
# ==========================================
def get_inventory():
    conn = connect_db()
    if not conn: return pd.DataFrame()
    try:
        # ĐÃ FIX: Chuyển CurrentStock sang bảng Inventory_Stock
        query = """
        SELECT 
            m.ModelCode AS [Mã SKU], 
            m.ModelName AS [Tên Sản Phẩm], 
            v.Color AS [Màu Sắc], 
            v.Size AS [Size], 
            ISNULL(inv.CurrentStock, 0) AS [Tồn Kho]
        FROM Product_Variants v
        JOIN Product_Models m ON v.ModelID = m.ModelID
        LEFT JOIN Inventory_Stock inv ON v.VariantID = inv.VariantID
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()

def update_stock(variant_id, stock_added):
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = """
        IF EXISTS (SELECT 1 FROM Inventory_Stock WHERE VariantID = ?)
            UPDATE Inventory_Stock SET CurrentStock = CurrentStock + ?, LastUpdated = GETDATE() WHERE VariantID = ?
        ELSE
            INSERT INTO Inventory_Stock (VariantID, CurrentStock, LastUpdated) VALUES (?, ?, GETDATE())
        """
        cursor.execute(query, (variant_id, stock_added, variant_id, variant_id, stock_added))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Lỗi update_stock: {e}")
        return False
    finally:
        conn.close()

# ==========================================
# 📈 4. DỮ LIỆU PHÂN TÍCH DASHBOARD
# ==========================================
# 🚀 HÀM VẼ BIỂU ĐỒ CHUẨN THEO SCRIPT SQL MỚI CỦA SẾP QUYỀN
def get_dashboard_trend_data():
    conn = connect_db()
    if not conn: return pd.DataFrame()
    try:
        query = """
        SELECT 
            FORMAT(C.RecordDate, 'dd/MM') AS Ngay, 
            ISNULL(S.TongBan, 0) AS ThucBan, 
            ISNULL(F.TongDuBao, 0) AS AIDuBao 
        FROM Calendar_Context C 
        LEFT JOIN (
            SELECT SaleDate, SUM(QuantitySold) as TongBan 
            FROM Internal_Sales GROUP BY SaleDate
        ) S ON CAST(C.RecordDate AS DATE) = CAST(S.SaleDate AS DATE)
        LEFT JOIN (
            SELECT TargetDate, SUM(PredictedMarketDemand) as TongDuBao 
            FROM AI_Forecast_Results GROUP BY TargetDate
        ) F ON CAST(C.RecordDate AS DATE) = CAST(F.TargetDate AS DATE)
        WHERE C.RecordDate <= GETDATE() 
        ORDER BY C.RecordDate DESC 
        OFFSET 0 ROWS FETCH NEXT 8 ROWS ONLY -- Lấy đúng 8 ngày Sếp vừa đưa
        """
        df = pd.read_sql(query, conn)
        # 🚀 LƯU Ý: Phải có dòng này thì ngày 11 mới nằm bên trái, 18 nằm bên phải
        return df.iloc[::-1]
    finally:
        conn.close()
def get_market_competitor_data():
    conn = connect_db()
    if not conn: return pd.DataFrame()
    try:
        query = """
        SELECT PM.ModelName, 
               AVG(S.ActualSellingPrice) AS GiaCuaMinh, 
               AVG(MT.CompetitorAvgPrice) AS GiaDoiThu 
        FROM Product_Models PM 
        JOIN Internal_Sales S ON PM.ModelID = (SELECT TOP 1 ModelID FROM Product_Variants WHERE VariantID = S.VariantID) 
        JOIN Market_Trends MT ON PM.ModelID = MT.ModelID 
        GROUP BY PM.ModelName
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()

def get_category_structure_data():
    conn = connect_db()
    if not conn: return pd.DataFrame()
    try:
        # ĐÃ FIX: Chuyển CurrentStock sang bảng Inventory_Stock
        query = """
        SELECT C.CategoryName, SUM(ISNULL(INV.CurrentStock, 0)) AS TongTonKho 
        FROM Categories C 
        JOIN Product_Models PM ON C.CategoryID = PM.CategoryID 
        JOIN Product_Variants PV ON PM.ModelID = PV.ModelID 
        LEFT JOIN Inventory_Stock INV ON PV.VariantID = INV.VariantID
        GROUP BY C.CategoryName
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()
    
# ==========================================
# 🤖 5. NGHIỆP VỤ BÁN HÀNG & AI DỰ BÁO
# ==========================================
def add_internal_sales(variant_id, sale_date, quantity_sold, actual_price):
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Internal_Sales (VariantID, SaleDate, QuantitySold, ActualSellingPrice) VALUES (?, ?, ?, ?)", (variant_id, sale_date, quantity_sold, actual_price))
        cursor.execute("UPDATE Inventory_Stock SET CurrentStock = CurrentStock - ?, LastUpdated = GETDATE() WHERE VariantID = ?", (quantity_sold, variant_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Lỗi giao dịch bán hàng: {e}")
        return False
    finally:
        conn.close()

def save_ai_forecast(variant_id, target_date, predicted_demand, suggested_restock, suggested_price=0):
    conn = connect_db()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO AI_Forecast_Results (VariantID, TargetDate, PredictedMarketDemand, SuggestedRestock, SuggestedPrice) VALUES (?, ?, ?, ?, ?)"
        cursor.execute(query, (variant_id, target_date, predicted_demand, suggested_restock, suggested_price))
        conn.commit()
        return True
    finally:
        conn.close()

# ==========================================
# 📥 6. XUẤT BÁO CÁO EXCEL (ĐÃ FIX BCNF)
# ==========================================
def export_inventory_to_excel(file_path="Bao_Cao_Ton_Kho.xlsx"):
    conn = connect_db()
    if not conn: return False
    try:
        # ĐÃ FIX: Chuyển CurrentStock sang bảng Inventory_Stock
        query = """
        SELECT 
            m.ModelCode AS [Mã SP], m.ModelName AS [Tên Sản Phẩm], 
            v.Color AS [Màu Sắc], v.Size AS [Kích Cỡ], ISNULL(inv.CurrentStock, 0) AS [Tồn Kho Thực Tế],
            ISNULL(f.PredictedMarketDemand, 0) AS [AI Dự Báo Bán Ra]
        FROM Product_Variants v
        INNER JOIN Product_Models m ON v.ModelID = m.ModelID
        LEFT JOIN Inventory_Stock inv ON v.VariantID = inv.VariantID
        LEFT JOIN (
            SELECT VariantID, PredictedMarketDemand FROM AI_Forecast_Results
            WHERE ForecastID IN (SELECT MAX(ForecastID) FROM AI_Forecast_Results GROUP BY VariantID)
        ) f ON v.VariantID = f.VariantID
        """
        df = pd.read_sql(query, conn)
        df.to_excel(file_path, index=False, engine='openpyxl')
        return True
    finally:
        conn.close()