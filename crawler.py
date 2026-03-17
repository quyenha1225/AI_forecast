import time
import urllib.parse
from datetime import date
import pyodbc
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# 1. THÔNG TIN KẾT NỐI DATABASE
# ==========================================
SERVER_NAME = 'TEN_MAY_CHU_CUA_BAN' 
DATABASE_NAME = 'Fashion_AI_Market'
USERNAME = 'sa' 
PASSWORD = 'mat_khau_cua_ban' 

# ==========================================
# 2. HÀM CÀO DỮ LIỆU TỪ SHOPEE
# ==========================================
def scrape_shopee(keyword, driver):
    print(f"\n🚀 Đang cào dữ liệu đối thủ cho: {keyword}")
    
    # [SỬA LỖI 2]: Bỏ qua thao tác gõ phím. Bắn thẳng từ khóa vào URL để tránh Anti-bot
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://shopee.vn/search?keyword={encoded_kw}"
    driver.get(url)
    
    results = []
    try:
        # [SỬA LỖI 3]: Explicit Wait. Chờ chủ động tối đa 10s, có data là lấy ngay
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-sqe='item'] | //li[contains(@class, 'col-xs-2-4')]"))
        )
        
        # Cuộn trang nhẹ để kích hoạt Lazy Load ảnh và cấu trúc DOM
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(1.5)
        
        # Lấy các thẻ chứa sản phẩm
        items = driver.find_elements(By.XPATH, "//div[@data-sqe='item'] | //li[contains(@class, 'col-xs-2-4')]")
        
        for item in items[:5]: # Chỉ lấy top 5 kết quả đầu tiên để đối chứng
            try:
                # [SỬA LỖI 1] & [SỬA LỖI 4]: Dùng XPath thực tế lấy đủ Tên gốc, Giá và URL
                
                # 1. Tên sản phẩm đối thủ
                name_el = item.find_element(By.XPATH, ".//div[@data-sqe='name']//div[1] | .//div[contains(@class, 'line-clamp')]")
                name = name_el.text.strip()
                
                # 2. Giá sản phẩm
                price_el = item.find_element(By.XPATH, ".//span[contains(text(), '₫')]/following-sibling::span")
                price_str = price_el.text.replace('.', '').replace(',', '').strip()
                
                # 3. Link URL để tạo Audit Trail (kiểm chứng lại khi cần)
                url_el = item.find_element(By.TAG_NAME, "a")
                link = url_el.get_attribute("href")
                
                if name and price_str.isdigit():
                    results.append({
                        'name': name[:500],
                        'price': float(price_str),
                        'url': link[:4000]
                    })
            except Exception:
                continue # Bỏ qua nếu là quảng cáo banner không có đủ cấu trúc
    except Exception:
        print(f"[!] Lỗi Timeout/Anti-bot khi tìm '{keyword}'")
        
    return results

# ==========================================
# 3. HÀM CHÍNH (MAIN EXECUTOR)
# ==========================================
if __name__ == "__main__":
    print("🔗 Đang kết nối Database Fashion_AI_Market...")
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};UID={USERNAME};PWD={PASSWORD}'
    # conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};Trusted_Connection=yes;'
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Chuẩn bị khóa ngoại (Foreign Keys)
        today = date.today().strftime('%Y-%m-%d')
        
        # 1. Đảm bảo ngày hôm nay có trong Calendar_Context
        cursor.execute("IF NOT EXISTS (SELECT 1 FROM Calendar_Context WHERE RecordDate = ?) INSERT INTO Calendar_Context (RecordDate, IsHoliday) VALUES (?, 0)", today, today)
        
        # 2. Đảm bảo có Platform 'Shopee' và lấy ID
        cursor.execute("IF NOT EXISTS (SELECT 1 FROM Platforms WHERE PlatformName = 'Shopee') INSERT INTO Platforms (PlatformName) VALUES ('Shopee')")
        cursor.execute("SELECT PlatformID FROM Platforms WHERE PlatformName = 'Shopee'")
        platform_id = cursor.fetchone()[0]
        conn.commit()
        
        # TỰ ĐỘNG LẤY DANH SÁCH SẢN PHẨM TỪ DATABASE
        cursor.execute("SELECT ModelID, ModelName FROM Product_Models")
        models_to_scrape = cursor.fetchall()
        
        if not models_to_scrape:
            print("⚠️ Bảng Product_Models đang trống. Bạn cần xử lý dữ liệu từ CSV bơm vào đây trước nhé!")
        else:
            print("🌐 Khởi động Trình duyệt Vượt Anti-Bot...")
            options = uc.ChromeOptions()
            options.add_argument('--disable-notifications')
            driver = uc.Chrome(options=options)
            
            # [SỬA LỖI 5]: Đổ dữ liệu chuẩn xác vào Crawler_Raw_Data với đầy đủ MatchedModelID
            sql_insert = """
                INSERT INTO Crawler_Raw_Data 
                (RecordDate, PlatformID, CompetitorProductName, ScrapedPrice, ProductURL, MatchedModelID)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            total_inserted = 0
            for model_id, model_name in models_to_scrape:
                scraped_data = scrape_shopee(model_name, driver)
                
                for data in scraped_data:
                    cursor.execute(sql_insert, today, platform_id, data['name'], data['price'], data['url'], model_id)
                    total_inserted += 1
                    
                conn.commit()
                time.sleep(3.5) # Nghỉ giữa các lượt cào để Shopee không khóa IP
                
            driver.quit()
            print(f"\n✅ HOÀN TẤT CHIẾN DỊCH! Đã cào và lưu {total_inserted} bản ghi đối chứng vào Crawler_Raw_Data.")
            
    except Exception as e:
        print(f"❌ LỖI HỆ THỐNG: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()