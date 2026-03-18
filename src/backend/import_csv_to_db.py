import pandas as pd
import pyodbc
import json
import os


# ==========================================
# BƯỚC 1: HÀM ĐỌC CẤU HÌNH & KẾT NỐI DB
# ==========================================
def get_db_connection():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'config.json')

        # Tìm file config nếu chạy ở thư mục khác
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(current_dir), 'config.json')

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={config['server']};"
            f"DATABASE={config['database']};"
            f"Trusted_Connection={'yes' if config['trusted_connection'] else 'no'};"
            f"TrustServerCertificate=yes;"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"❌ Lỗi đọc config.json hoặc kết nối DB: {e}")
        return None


# ==========================================
# BƯỚC 2: ĐỌC VÀ TIỀN XỬ LÝ CSV
# ==========================================
print("📦 Đang đọc và nghiền nát file CSV...")
# Tìm đường dẫn file CSV (dựa theo cấu trúc: Encommerce_AI_App/data/raw/scanner_data.csv)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
csv_path = os.path.join(project_root, 'data', 'raw', 'scanner_data.csv')

try:
    df = pd.read_csv(csv_path)
except FileNotFoundError:
    print(f"❌ KHÔNG TÌM THẤY FILE CSV TẠI: {csv_path}")
    print("Sếp Quyền hãy kiểm tra lại xem file scanner_data.csv đã nằm đúng trong thư mục data/raw/ chưa nhé!")
    exit()

# 1. Bóc tách Danh mục
df_categories = df[['SKU_Category']].drop_duplicates().reset_index(drop=True)

tu_dien_bien_dich = {
    'N8U': 'Áo thun nam', 'R6E': 'Quần jean nam', 'LPF': 'Áo sơ mi nữ công sở',
    'P42': 'Váy liền thân', 'U5F': 'Quần short thể thao', '0H2': 'Áo khoác gió mùa đông',
    'IEV': 'Áo polo nam', 'FEW': 'Quần âu nữ', '29A': 'Áo len cổ lọ',
    'H15': 'Giày sneaker thể thao', 'Q4N': 'Túi xách đeo chéo', 'OXH': 'Đồ lót nam',
    'FU5': 'Set 5 đôi tất cotton', '8HU': 'Quần kaki nam', 'J4R': 'Áo chống nắng',
    '01F': 'Đồ bộ mặc nhà', 'XG4': 'Mũ lưỡi trai', 'TW8': 'Kính mát thời trang',
    '6BZ': 'Thắt lưng da nam', 'SJS': 'Khăn lụa quàng cổ'
}
df_categories['CategoryName'] = df_categories['SKU_Category'].map(tu_dien_bien_dich).fillna('Sản phẩm chưa phân loại')

# 2. Bóc tách Mẫu sản phẩm
df_models = df[['SKU', 'SKU_Category']].drop_duplicates().reset_index(drop=True)
df_models['ModelName'] = df_models['SKU_Category'].map(tu_dien_bien_dich).fillna('SP Khác') + " - Mã " + df_models[
    'SKU'].astype(str)
df_models['BasePrice'] = 250000  # Gán giá mặc định ban đầu

print(f"✅ Đã tìm thấy {len(df_categories)} Danh mục và {len(df_models)} Mã Sản phẩm.")

# ==========================================
# BƯỚC 3: BƠM DỮ LIỆU VÀO SQL CHUẨN BCNF
# ==========================================
print("\n🔗 Đang kết nối tới Database...")
conn = get_db_connection()

if not conn:
    exit()

try:
    cursor = conn.cursor()

    # --- THÁC 1: BƠM DANH MỤC ---
    print("⏳ Đang bơm bảng Categories...")
    for _, row in df_categories.iterrows():
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Categories WHERE CategoryName = ?)
            INSERT INTO Categories (CategoryName) VALUES (?)
        """, (row['CategoryName'], row['CategoryName']))
    conn.commit()
    print("✅ Đã bơm xong Danh mục!")

    # Lấy map ID Danh mục
    cursor.execute("SELECT CategoryName, CategoryID FROM Categories")
    cat_id_map = dict(cursor.fetchall())

    # --- THÁC 2: BƠM PRODUCT MODELS ---
    print("⏳ Đang bơm bảng Product_Models (Có thể mất vài chục giây)...")
    count_models = 0
    for _, row in df_models.iterrows():
        cat_name = tu_dien_bien_dich.get(row['SKU_Category'], 'Sản phẩm chưa phân loại')
        cat_id = cat_id_map.get(cat_name)

        if cat_id:
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM Product_Models WHERE ModelCode = ?)
                INSERT INTO Product_Models (ModelCode, ModelName, CategoryID, BasePrice) VALUES (?, ?, ?, ?)
            """, (str(row['SKU']), str(row['SKU']), row['ModelName'], cat_id, row['BasePrice']))
            count_models += 1

            if count_models % 500 == 0:
                conn.commit()
                print(f"   ...Đã bơm {count_models} mã Models...")
    conn.commit()
    print(f"✅ Đã bơm xong {count_models} Mẫu Mã Sản Phẩm!")

    # --- THÁC 3: TẠO PRODUCT VARIANTS (BIẾN THỂ) ---
    print("⏳ Đang tự động tạo Biến thể mặc định (Freesize/Đa sắc)...")
    cursor.execute("""
        INSERT INTO Product_Variants (ModelID, Color, Size)
        SELECT ModelID, N'Đa sắc', 'FreeSize' 
        FROM Product_Models PM
        WHERE NOT EXISTS (
            SELECT 1 FROM Product_Variants PV WHERE PV.ModelID = PM.ModelID
        )
    """)
    conn.commit()
    print("✅ Đã tạo xong Biến Thể!")

    # --- THÁC 4: TẠO INVENTORY STOCK (KHO HÀNG TRỐNG) ---
    print("⏳ Đang đồng bộ kho hàng...")
    cursor.execute("""
        INSERT INTO Inventory_Stock (VariantID, CurrentStock, LastUpdated)
        SELECT VariantID, 0, GETDATE()
        FROM Product_Variants PV
        WHERE NOT EXISTS (
            SELECT 1 FROM Inventory_Stock INV WHERE INV.VariantID = PV.VariantID
        )
    """)
    conn.commit()
    print("✅ Đã đồng bộ Kho hàng thành công!")

    print("\n🎉🎉🎉 CHÚC MỪNG ANH QUYỀN ĐẸP TRAI! ĐÃ BƠM TOÀN BỘ DATA CHUẨN CHỈ!")

except Exception as e:
    print(f"❌ LỖI TRONG QUÁ TRÌNH BƠM DỮ LIỆU: {e}")
    conn.rollback()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals() and conn:
        conn.close()