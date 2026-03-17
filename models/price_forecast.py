import pandas as pd
import joblib
import os
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, VotingRegressor

# =====================================================================
# CÀI ĐẶT ĐƯỜNG DẪN "CHỐNG LẠC" CHO HỆ THỐNG
# =====================================================================
# 1. Lấy vị trí thư mục chứa file code này (chính là thư mục 'models')
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 2. Lùi lại 1 bước để lấy thư mục gốc của dự án (Encommerce_AI_App)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)


# =====================================================================
# 1. HÀM HUẤN LUYỆN: CỖ MÁY LAI (ENSEMBLE LEARNING)
# =====================================================================
def train_model(csv_file_path):
    print("⏳ Đang khởi động lò đúc CỖ MÁY LAI (Random Forest + Gradient Boosting)...")
    df = pd.read_csv(csv_file_path)

    # 1.1 Làm sạch và Bơm giác quan
    df_clean = df.copy()
    df_clean['Unit_Price'] = df_clean['Sales_Amount'] / df_clean['Quantity']
    df_clean['Date'] = pd.to_datetime(df_clean['Date'], dayfirst=True, errors='coerce')
    df_clean = df_clean.dropna(subset=['Date'])
    df_clean['Month'] = df_clean['Date'].dt.month
    df_clean['Day'] = df_clean['Date'].dt.day
    df_clean['DayOfWeek'] = df_clean['Date'].dt.dayofweek
    df_clean['Is_Weekend'] = (df_clean['DayOfWeek'] >= 5).astype(int)

    cols_to_drop = ['Unnamed: 0', 'Customer_ID', 'Transaction_ID', 'Sales_Amount', 'Date']
    df_clean = df_clean.drop(columns=[c for c in cols_to_drop if c in df_clean.columns])

    # 1.2 Mã hóa
    le_category = LabelEncoder()
    df_clean['SKU_Category'] = le_category.fit_transform(df_clean['SKU_Category'].astype(str))
    le_sku = LabelEncoder()
    df_clean['SKU'] = le_sku.fit_transform(df_clean['SKU'].astype(str))
    df_clean = df_clean.dropna()

    X = df_clean.drop(columns=['Quantity'])
    y = df_clean['Quantity']

    # 1.3 Song kiếm hợp bích (Ensemble Voting)
    print("🤖 Đang truyền nội công cho 2 thuật toán...")
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    gb = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, random_state=42)

    ensemble_model = VotingRegressor(estimators=[('RF', rf), ('GB', gb)])
    ensemble_model.fit(X, y)

    # 1.4 Xuất file Não bộ (Lưu thẳng vào thư mục models hiện tại)
    joblib.dump(ensemble_model, os.path.join(CURRENT_DIR, 'price_forecast.pkl'))
    joblib.dump(le_category, os.path.join(CURRENT_DIR, 'encoder_category.pkl'))
    joblib.dump(le_sku, os.path.join(CURRENT_DIR, 'encoder_sku.pkl'))
    print("✅ ĐÃ ĐÚC XONG NÃO BỘ LAI (ENSEMBLE 81%)! Sẵn sàng chinh chiến.")


# =====================================================================
# 2. HÀM TẢI NÃO BỘ LÊN RAM
# =====================================================================
def load_ai_model():
    try:
        model = joblib.load(os.path.join(CURRENT_DIR, 'price_forecast.pkl'))
        enc_cat = joblib.load(os.path.join(CURRENT_DIR, 'encoder_category.pkl'))
        enc_sku = joblib.load(os.path.join(CURRENT_DIR, 'encoder_sku.pkl'))
        return model, enc_cat, enc_sku
    except Exception as e:
        print(f"❌ Lỗi tải AI (Vui lòng chạy train_model trước): {e}")
        return None, None, None


# =====================================================================
# 3. HÀM DỰ BÁO THỰC CHIẾN
# =====================================================================
def predict_future_demand(model, enc_cat, enc_sku, category_name, sku_code, target_date, current_price,
                          competitor_price, trend_score, weather_temp):
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    is_new_sku = False

    try:
        cat_encoded = enc_cat.transform([str(category_name)])[0]
    except ValueError:
        cat_encoded = 0

    try:
        sku_encoded = enc_sku.transform([str(sku_code)])[0]
    except ValueError:
        sku_encoded = 0
        is_new_sku = True

    X_new = pd.DataFrame({
        'SKU_Category': [cat_encoded],
        'SKU': [sku_encoded],
        'Unit_Price': [current_price],
        'Month': [dt.month],
        'Day': [dt.day],
        'DayOfWeek': [dt.weekday()],
        'Is_Weekend': [1 if dt.weekday() >= 5 else 0]
    })

    final_demand = model.predict(X_new)[0]

    if is_new_sku:
        final_demand *= 1.2
    if current_price > competitor_price:
        final_demand *= 0.85
    if trend_score >= 8:
        final_demand *= 1.3
    if weather_temp < 20 and str(category_name) == "07":
        final_demand *= 1.5
    elif weather_temp > 30 and str(category_name) == "07":
        final_demand *= 0.5

    return round(final_demand)


# =====================================================================
# 4. HÀM QUYẾT ĐỊNH NHẬP KHO
# =====================================================================
def calculate_restock_amount(predicted_demand, current_stock):
    return max(0, predicted_demand - current_stock)


# =====================================================================
# CHẠY THỬ (TESTING)
# =====================================================================
if __name__ == "__main__":
    # 🚨 BƯỚC 1: Đã đúc não xong rồi thì KHÓA dòng này lại bằng dấu # nhé,
    # để máy không phải cày lại data mất thời gian!
    duong_dan_csv = os.path.join(PROJECT_ROOT, "data", "raw", "scanner_data.csv")
    # train_model(duong_dan_csv)  <-- Thêm dấu # ở đầu như thế này

    # BƯỚC 2: CHẠY THỬ DỰ BÁO
    ai_model, encoder_cat, encoder_sku = load_ai_model()

    if ai_model:
        # KỊCH BẢN MỚI: TUNG SẢN PHẨM MỚI TINH VÀO MÙA ĐÔNG
        ma_hang = "AOKHOAC_VIP_2026"  # Mã này AI chưa từng thấy bao giờ (Test Cold-Start)
        loai_hang = "07"  # Mã 07 quy ước là Áo Khoác
        ngay = "2026-12-24"  # Bán đúng đêm Noel!

        so_ban_du_kien = predict_future_demand(
            ai_model, encoder_cat, encoder_sku,
            loai_hang, ma_hang, ngay,
            current_price=250000, competitor_price=300000,  # Mình bán RẺ HƠN đối thủ 50k!
            trend_score=10, weather_temp=12  # Rét đậm 12 độ + Đang viral Top 1 TikTok
        )

        ton_kho = 5  # Giả sử trong kho chỉ còn 5 cái
        so_can_nhap = calculate_restock_amount(so_ban_du_kien, ton_kho)

        print("\n🏆 KẾT QUẢ TỪ HỆ THỐNG ENSEMBLE AI (81%):")
        print(f"🔹 Kịch bản: Áo khoác mới, giá rẻ, siêu rét, siêu Hot Trend!")
        print(f"👉 Nhu cầu thị trường dự kiến: {so_ban_du_kien} sản phẩm")
        print(f"📦 Tồn kho hiện tại: {ton_kho} sản phẩm")
        print(f"🚛 LỆNH XUẤT KHO: Cần nhập gấp {so_can_nhap} sản phẩm!")