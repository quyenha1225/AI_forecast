import time
import pyodbc
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Danh sách tên sản phẩm bạn lấy được từ file CSV bước trước
danh_sach_san_pham = [
    'Áo thun nam',
    'Quần jean nam',
    'Áo sơ mi nữ công sở'
]

def lay_gia_shopee(ten_san_pham, driver):
    print(f"\nĐang tìm kiếm giá cho: {ten_san_pham}")
    driver.get('https://shopee.vn/')
    time.sleep(3) 
    
    try:
        search_box = driver.find_element(By.CSS_SELECTOR, "input.shopee-searchbar-input__input")
        search_box.clear()
        search_box.send_keys(ten_san_pham)
        search_box.send_keys(Keys.RETURN)
        
        time.sleep(4) 
        
        # Cần F12 để tìm đúng class chứa giá tiền thực tế của Shopee
        elements_gia = driver.find_elements(By.CSS_SELECTOR, "span.price-class-name-vi-du") 
        
        danh_sach_gia = []
        for el in elements_gia[:5]: 
            gia_text = el.text.replace('₫', '').replace('.', '').strip()
            if gia_text.isdigit():
                danh_sach_gia.append(int(gia_text))
                
        if danh_sach_gia:
            gia_trung_binh = sum(danh_sach_gia) / len(danh_sach_gia)
            print(f"-> Giá trung bình ước tính: {gia_trung_binh:,.0f} VNĐ")
            return gia_trung_binh
        else:
            print("-> Không tìm thấy giá hợp lệ.")
            return 0
            
    except Exception as e:
        print(f"-> Lỗi khi tìm {ten_san_pham}: Có thể bị chặn hoặc sai class HTML.")
        return 0

# ==========================================
# HÀM CHÍNH (MAIN)
# ==========================================
if __name__ == "__main__":
    print("Khởi động trình duyệt ẩn danh...")
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    
    ket_qua_gia = {}
    
    for sp in danh_sach_san_pham: 
        gia = lay_gia_shopee(sp, driver)
        ket_qua_gia[sp] = gia
        time.sleep(5) 
        
    driver.quit()
    
    print("\n--- ĐÃ CÀO XONG! ĐANG BƠM VÀO SQL SERVER ---")
    
    # =================================================================
    # ĐÂY LÀ ĐOẠN CODE LƯU VÀO DATABASE 
    # =================================================================
    SERVER_NAME = 'TEN_MAY_CHU_CUA_BAN' # Điền tên Server của bạn vào đây
    DATABASE_NAME = 'Ten_Database_Cua_Ban' # Điền tên Database của bạn vào đây
    USERNAME = 'sa' 
    PASSWORD = 'Mat_khau_cua_ban' 

    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};UID={USERNAME};PWD={PASSWORD}'
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Giả sử bạn tạo một bảng tên là GiaThiTruong để lưu giá cào được
        sql_insert = """
            INSERT INTO GiaThiTruong (Ten_San_Pham, Gia_Trung_Binh)
            VALUES (?, ?)
        """
        
        count = 0
        for ten_sp, gia_tb in ket_qua_gia.items():
            if gia_tb > 0: # Chỉ lưu những sản phẩm cào được giá
                cursor.execute(sql_insert, ten_sp, gia_tb)
                count += 1
                
        conn.commit()
        print(f"Hoàn tất! Đã lưu thành công giá của {count} sản phẩm vào Database.")
        
    except Exception as e:
        print(f"Lỗi khi kết nối hoặc lưu vào Database: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()