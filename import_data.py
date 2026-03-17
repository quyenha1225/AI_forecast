import pandas as pd
import pyodbc

# ==========================================
# BƯỚC 1: ĐỌC VÀ XỬ LÝ DỮ LIỆU CSV
# ==========================================

print("Đang đọc file dữ liệu...")
# 1. Đọc file csv của bạn
df = pd.read_csv('scanner_data.csv')

# 2. Lấy danh sách các mã sản phẩm (SKU) và Danh mục (SKU_Category) duy nhất
df_san_pham = df[['SKU', 'SKU_Category']].drop_duplicates().reset_index(drop=True)

# 3. Tạo từ điển "biên dịch" mã danh mục thành tên sản phẩm
tu_dien_bien_dich = {
    'N8U': 'Áo thun nam',
    'R6E': 'Quần jean nam',
    'LPF': 'Áo sơ mi nữ công sở',
    'P42': 'Váy liền thân',
    'U5F': 'Quần short thể thao',
    '0H2': 'Áo khoác gió mùa đông',
    'IEV': 'Áo polo nam',
    'FEW': 'Quần âu nữ',
    '29A': 'Áo len cổ lọ',
    'H15': 'Giày sneaker thể thao',
    'Q4N': 'Túi xách đeo chéo',
    'OXH': 'Đồ lót nam',
    'FU5': 'Set 5 đôi tất cotton',
    '8HU': 'Quần kaki nam',
    'J4R': 'Áo chống nắng',
    '01F': 'Đồ bộ mặc nhà',
    'XG4': 'Mũ lưỡi trai',
    'TW8': 'Kính mát thời trang',
    '6BZ': 'Thắt lưng da nam',
    'SJS': 'Khăn lụa quàng cổ'
}

# 4. Tạo cột 'Ten_San_Pham' dựa trên từ điển biên dịch
df_san_pham['Ten_San_Pham'] = df_san_pham['SKU_Category'].map(tu_dien_bien_dich)

# Nếu có mã nào chưa có trong từ điển, ta gán tạm là "Sản phẩm chưa phân loại"
df_san_pham['Ten_San_Pham'] = df_san_pham['Ten_San_Pham'].fillna('Sản phẩm chưa phân loại')

print(f"Đã xử lý xong {len(df_san_pham)} mã sản phẩm duy nhất.")
print("Dữ liệu xem trước:")
print(df_san_pham.head())

# (Tùy chọn) Lưu file danh sách sản phẩm đã biên dịch ra máy tính để xem lại trước khi import
df_san_pham.to_csv('danh_sach_san_pham_da_dich.csv', index=False, encoding='utf-8-sig')


# ==========================================
# BƯỚC 2: BƠM DỮ LIỆU VÀO SQL SERVER
# ==========================================

print("\nĐang kết nối SQL Server...")

# 5. Cấu hình chuỗi kết nối SQL Server
# LƯU Ý: THAY ĐỔI CÁC THÔNG TIN DƯỚI ĐÂY CHO ĐÚNG VỚI MÁY CHỦ CỦA BẠN
SERVER_NAME = 'TEN_MAY_CHU_CUA_BAN' # Ví dụ: 'localhost\SQLEXPRESS'
DATABASE_NAME = 'Ten_Database_Cua_Ban'
USERNAME = 'sa' # Nếu dùng quyền Windows (Trusted Connection) thì có thể bỏ UID, PWD
PASSWORD = 'Mat_khau_cua_ban'

try:
    # Chuỗi kết nối dùng tài khoản SQL
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};UID={USERNAME};PWD={PASSWORD}'
    
    # Nếu bạn dùng chứng thực Windows (Windows Authentication), hãy đổi thành chuỗi này:
    # conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};Trusted_Connection=yes;'
    
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    print("Kết nối thành công! Đang bơm dữ liệu...")

    # 6. Quét qua dữ liệu và chèn (INSERT) vào SQL Server
    # Giả sử trong SQL Server của bạn có bảng tên là `Products` gồm các cột: `SKU`, `SKU_Category`, `Product_Name`
    sql_insert = """
        INSERT INTO Products (SKU, SKU_Category, Product_Name)
        VALUES (?, ?, ?)
    """
    
    # Biến đếm số lượng bản ghi được insert thành công
    count = 0 
    
    for index, row in df_san_pham.iterrows():
        try:
            cursor.execute(sql_insert, row['SKU'], row['SKU_Category'], row['Ten_San_Pham'])
            count += 1
            
            # Để tránh treo máy, cứ 1000 dòng thì lưu (commit) một lần
            if count % 1000 == 0:
                conn.commit()
                print(f"Đã bơm {count} dòng...")
        except Exception as e:
            print(f"Lỗi khi chèn dòng SKU {row['SKU']}: {e}")

    # Commit các dữ liệu còn lại
    conn.commit()
    print(f"Hoàn tất! Đã bơm thành công {count} sản phẩm vào Database.")

except Exception as e:
    print(f"Không thể kết nối SQL Server hoặc lỗi Database: {e}")
finally:
    # 7. Đóng kết nối
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()