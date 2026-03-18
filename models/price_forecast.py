import pandas as pd
import joblib
import os
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, VotingRegressor

# =====================================================================
# CÀI ĐẶT ĐƯỜNG DẪN "CHỐNG LẠC" CHO HỆ THỐNG
# =====================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)


# =====================================================================
# 1. HÀM HUẤN LUYỆN: CỖ MÁY LAI (HỌC TỔNG CẦU THEO NGÀY)
# =====================================================================
def train_model(csv_file_path):
    print("⏳ Đang khởi động lò đúc CỖ MÁY LAI (Random Forest + Gradient Boosting)...")
    df = pd.read_csv(csv_file_path)

    df_clean = df.copy()
    df_clean['Date'] = pd.to_datetime(df_clean['Date'], dayfirst=True, errors='coerce')
    df_clean = df_clean.dropna(subset=['Date'])

    # 🚀 BƯỚC ĐỘT PHÁ: Gom nhóm cộng dồn doanh số theo TỪNG NGÀY
    df_grouped = df_clean.groupby(['Date', 'SKU_Category', 'SKU']).agg({
        'Quantity': 'sum',  # Tổng số lượng bán ra TRONG 1 NGÀY
        'Sales_Amount': 'sum'  # Tổng tiền thu được TRONG 1 NGÀY
    }).reset_index()

    # Tính lại giá bán trung bình của ngày hôm đó
    df_grouped['Unit_Price'] = df_grouped['Sales_Amount'] / df_grouped['Quantity']

    # Bóc tách giác quan thời gian
    df_grouped['Month'] = df_grouped['Date'].dt.month
    df_grouped['Day'] = df_grouped['Date'].dt.day
    df_grouped['DayOfWeek'] = df_grouped['Date'].dt.dayofweek
    df_grouped['Is_Weekend'] = (df_grouped['DayOfWeek'] >= 5).astype(int)

    le_category = LabelEncoder()
    df_grouped['SKU_Category'] = le_category.fit_transform(df_grouped['SKU_Category'].astype(str))

    le_sku = LabelEncoder()
    df_grouped['SKU'] = le_sku.fit_transform(df_grouped['SKU'].astype(str))

    df_grouped = df_grouped.dropna()

    # Khóa mục tiêu vào 6 cột này
    X = df_grouped[['SKU_Category', 'SKU', 'Month', 'Day', 'DayOfWeek', 'Is_Weekend', 'Unit_Price']]
    y = df_grouped['Quantity']

    print("🤖 Đang truyền nội công cho 2 thuật toán...")
    rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42)
    gb = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, random_state=42)

    ensemble_model = VotingRegressor(estimators=[('RF', rf), ('GB', gb)])
    ensemble_model.fit(X, y)

    # Lưu não bộ
    joblib.dump(ensemble_model, os.path.join(CURRENT_DIR, 'price_forecast.pkl'))
    joblib.dump(le_category, os.path.join(CURRENT_DIR, 'encoder_category.pkl'))
    joblib.dump(le_sku, os.path.join(CURRENT_DIR, 'encoder_sku.pkl'))
    print("✅ ĐÃ ĐÚC XONG NÃO BỘ DAILY FORECAST! Sẵn sàng chinh chiến.")


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
# 3. HÀM DỰ BÁO THỰC CHIẾN MỖI NGÀY
# =====================================================================
def predict_future_demand(model, enc_cat, enc_sku, category_name, sku_code, target_date, current_price,
                          competitor_price, trend_score, weather_temp):
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
    except:
        dt = datetime.now()

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

    # Đưa vào đúng 6 cột như lúc học
    X_new = pd.DataFrame({
        'SKU_Category': [cat_encoded],
        'SKU': [sku_encoded],
        'Month': [dt.month],
        'Day': [dt.day],
        'DayOfWeek': [dt.weekday()],
        'Is_Weekend': [1 if dt.weekday() >= 5 else 0],
        'Unit_Price': [current_price]
    })
    X_new = X_new[['SKU_Category', 'SKU', 'Month', 'Day', 'DayOfWeek', 'Is_Weekend', 'Unit_Price']]

    base_demand = model.predict(X_new)[0]

    # --- LUẬT KINH DOANH LEADER QUYỀN ---
    multiplier = 1.0

    if is_new_sku: multiplier *= 1.3
    if current_price > competitor_price:
        multiplier *= 0.7
    elif current_price < competitor_price:
        multiplier *= 1.4
    if trend_score >= 8: multiplier *= (1 + (trend_score * 0.15))

    # Logic thời tiết cho áo ấm
    if weather_temp < 20 and ("áo khoác" in str(category_name).lower() or "áo len" in str(category_name).lower()):
        multiplier *= 2.0
    elif weather_temp > 28 and ("áo khoác" in str(category_name).lower() or "áo len" in str(category_name).lower()):
        multiplier *= 0.2

    final_demand = base_demand * multiplier

    return max(0, int(final_demand))


# =====================================================================
# 4. HÀM QUYẾT ĐỊNH NHẬP KHO
# =====================================================================
def calculate_restock_amount(predicted_demand, current_stock):
    return max(0, predicted_demand - current_stock)


# =====================================================================
# CHẠY ĐỂ ĐÚC NÃO (CHẠY 1 LẦN)
# =====================================================================
if __name__ == "__main__":
    # 🚨 SẾP MỞ KHÓA 2 DÒNG NÀY VÀ CHẠY FILE NÀY ĐỂ ĐÚC LẠI NÃO NHÉ
    duong_dan_csv = os.path.join(PROJECT_ROOT, "data", "raw", "scanner_data.csv")
    train_model(duong_dan_csv)

    # Test thử
    ai_model, encoder_cat, encoder_sku = load_ai_model()
    if ai_model:
        so_ban = predict_future_demand(ai_model, encoder_cat, encoder_sku, "Áo khoác gió mùa đông", "0H21",
                                       "2026-12-24", 250000, 300000, 10, 12)
        print(f"\n🏆 TEST: Đêm Noel rét 12 độ, dự kiến chốt được {so_ban} đơn áo khoác!")