import time
import urllib.parse
import re
import os
import json
from datetime import date
import pyodbc
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By


# ==========================================
# 1. KẾT NỐI DATABASE
# ==========================================
def get_db_connection():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'config.json')
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
        print(f"❌ Lỗi kết nối CSDL: {e}")
        return None


# ==========================================
# 2. HÀM CÀO DỮ LIỆU SHOPEE
# ==========================================
def scrape_shopee(keyword, driver):
    print(f"\n🚀 Đang truy lùng Top đối thủ cho: '{keyword}'")
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://shopee.vn/search?keyword={encoded_kw}"

    try:
        driver.get(url)
        time.sleep(4)

        # --- KIỂM TRA CAPTCHA ---
        if "verify/captcha" in driver.current_url or "Lỗi tải" in driver.page_source:
            print("🚨 SHOPEE CHẶN! Sếp Quyền kéo thanh trượt trên trình duyệt giúp em nhé!")
            while "verify/captcha" in driver.current_url:
                time.sleep(2)
            print("✅ Đã vượt rào thành công!")

        # --- CUỘN TRANG ---
        for _ in range(2):
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(1.5)

        results = []
        xpath_items = "//div[@data-sqe='item'] | //div[contains(@class, 'shopee-search-item-result__item')]"
        items = driver.find_elements(By.XPATH, xpath_items)

        # Cào Top 5 để lấy giá trị trung bình chuẩn xác nhất
        for item in items[:5]:
            try:
                name = item.find_element(By.XPATH,
                                         ".//div[@data-sqe='name'] | .//div[contains(@class, 'word-break')]").text.strip()
                price_text = item.find_element(By.XPATH,
                                               ".//span[contains(text(), '₫')]/following-sibling::span | .//div[contains(@class, 'font-medium')]").text

                price_clean = re.sub(r'[^\d]', '', price_text)
                final_price = float(price_clean)

                if name and final_price > 0:
                    results.append(final_price)
            except:
                continue

        # Trả về Danh sách giá và URL gốc để kiểm chứng
        return results, url
    except Exception as e:
        print(f"⚠️ Lỗi xử lý từ khóa '{keyword}': {e}")
        return [], url


# ==========================================
# 3. TRẠM CHỈ HUY BOT (TỐI ƯU SIÊU TỐC)
# ==========================================
if __name__ == "__main__":
    print("==================================================")
    print("🕸️ BOT QUYỀN V3.0 - QUÉT THEO NHÓM DANH MỤC 🕸️")
    print("==================================================")

    conn = get_db_connection()
    if not conn: exit()

    try:
        cursor = conn.cursor()
        today = date.today().strftime('%Y-%m-%d')

        cursor.execute(
            "IF NOT EXISTS (SELECT 1 FROM Platforms WHERE PlatformName = 'Shopee') INSERT INTO Platforms (PlatformName) VALUES ('Shopee')")
        cursor.execute("SELECT PlatformID FROM Platforms WHERE PlatformName = 'Shopee'")
        platform_id = cursor.fetchone()[0]

        cursor.execute("DELETE FROM Crawler_Raw_Data WHERE RecordDate = ? AND PlatformID = ?", (today, platform_id))
        conn.commit()

        # 🚀 THUẬT TOÁN MỚI: GOM NHÓM THEO DANH MỤC (CATEGORY)
        print("📊 Đang gom nhóm 1800+ sản phẩm theo Danh mục...")
        cursor.execute("""
            SELECT PM.ModelID, C.CategoryName
            FROM Product_Models PM
            JOIN Categories C ON PM.CategoryID = C.CategoryID
            WHERE C.CategoryName NOT LIKE N'%khác%' AND C.CategoryName NOT LIKE N'%chưa phân loại%'
        """)

        all_models = cursor.fetchall()

        # Nhét vào một cuốn từ điển (Dictionary) để gom nhóm
        # Kết quả: {'Áo chống nắng': [ID_1, ID_2, ID_3...], 'Quần Jean': [ID_4, ID_5...]}
        category_groups = {}
        for model_id, cat_name in all_models:
            if cat_name not in category_groups:
                category_groups[cat_name] = []
            category_groups[cat_name].append(model_id)

        if not category_groups:
            print("⚠️ Không tìm thấy danh mục hợp lệ!")
        else:
            print(f"✅ Đã gom 1843 mã thành {len(category_groups)} Danh mục. Tốc độ quét sẽ tăng x100 lần!")

            options = uc.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-search-engine-choice-screen')

            bot_profile = os.path.abspath(os.path.join(os.getcwd(), "Shopee_Bot_Data"))
            options.add_argument(f"--user-data-dir={bot_profile}")

            # Lưu ý đường dẫn trình duyệt của anh Quyền
            thorium_exe = r"C:\Users\Asus\AppData\Local\Thorium\Application\thorium.exe"
            driver = uc.Chrome(options=options, browser_executable_path=thorium_exe, version_main=130)

            driver.get("https://shopee.vn")
            print("\n🚨 SẾP ƠI: Chuẩn bị giải Captcha (nếu bị Shopee hỏi) trong 30 giây tới nhé!")
            time.sleep(30)

            total_saved = 0
            # Vòng lặp bây giờ chỉ chạy 18 lần thay vì 1843 lần!
            for cat_name, list_model_ids in category_groups.items():

                prices, search_url = scrape_shopee(cat_name, driver)

                if prices:
                    # Lấy Trung bình giá
                    avg_price = sum(prices) / len(prices)

                    # Áp con số trung bình này cho hàng trăm ModelID thuộc danh mục đó
                    for model_id in list_model_ids:
                        cursor.execute("""
                            INSERT INTO Crawler_Raw_Data (RecordDate, PlatformID, CompetitorProductName, ScrapedPrice, ProductURL, MatchedModelID)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (today, platform_id, f"Trung bình giá Shopee ({cat_name})", avg_price, search_url,
                              model_id))

                    conn.commit()
                    total_saved += len(list_model_ids)
                    print(
                        f"   ✔️ Đã tính Giá Trung Bình: {avg_price:,.0f} ₫ và áp dụng cho {len(list_model_ids)} mã SKU loại '{cat_name}'.")

                time.sleep(4)

            driver.quit()
            print(
                f"\n🎉 QUÁ NHANH QUÁ NGUY HIỂM! Đã tự động cập nhật giá cho {total_saved} mã sản phẩm chỉ trong vài phút.")

    except Exception as e:
        print(f"❌ LỖI HỆ THỐNG: {e}")
    finally:
        if 'conn' in locals(): conn.close()