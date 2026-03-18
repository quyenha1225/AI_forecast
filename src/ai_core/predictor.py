import pandas as pd
import joblib
import os
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, VotingRegressor


# =====================================================================
# 1. HÀM HUẤN LUYỆN: CỖ MÁY LAI (HỌC DOANH SỐ MỖI NGÀY)
# =====================================================================
def train_model(csv_file_path):
    print("⏳ Đang khởi động lò đúc CỖ MÁY LAI (Random Forest + Gradient Boosting)...")
    df = pd.read_csv(csv_file_path)

    df_clean = df.copy()
    df_clean['Date'] = pd.to_datetime(df_clean['Date'], dayfirst=True, errors='coerce')
    df_clean = df_clean.dropna(subset=['Date'])

    # 🚀 BƯỚC ĐỘT PHÁ CỦA SẾP QUYỀN: Gom nhóm CỘNG DỒN TỔNG SỐ LƯỢNG theo TỪNG NGÀY
    df_grouped = df_clean.groupby(['Date', 'SKU_Category', 'SKU']).agg({
        'Quantity': 'sum',  # Tổng số lượng bán ra TRONG 1 NGÀY
        'Sales_Amount': 'sum'  # Tổng tiền thu được TRONG 1 NGÀY
    }).reset_index()

    # Tính lại giá bán trung bình của ngày hôm đó
    df_grouped['Unit_Price'] = df_grouped['Sales_Amount'] / df_grouped['Quantity']

    # Bóc tách giác quan thời gian từ Cột Ngày
    df_grouped['Month'] = df_grouped['Date'].dt.month
    df_grouped['Day'] = df_grouped['Date'].dt.day
    df_grouped['DayOfWeek'] = df_grouped['Date'].dt.dayofweek
    df_grouped['Is_Weekend'] = (df_grouped['DayOfWeek'] >= 5).astype(int)

    le_category = LabelEncoder()
    df_grouped['SKU_Category'] = le_category.fit_transform(df_grouped['SKU_Category'].astype(str))

    le_sku = LabelEncoder()
    df_grouped['SKU'] = le_sku.fit_transform(df_grouped['SKU'].astype(str))

    df_grouped = df_grouped.dropna()

    # Chọn đúng 6 cột giác quan này để học
    X = df_grouped[['SKU_Category', 'SKU', 'Month', 'Day', 'DayOfWeek', 'Is_Weekend', 'Unit_Price']]
    y = df_grouped['Quantity']  # Cột mục tiêu: TỔNG BÁN MỖI NGÀY

    print("🤖 Đang truyền nội công cho 2 thuật toán...")
    rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42)
    gb = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, random_state=42)

    ensemble_model = VotingRegressor(estimators=[('RF', rf), ('GB', gb)])
    ensemble_model.fit(X, y)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'models'))
    os.makedirs(models_dir, exist_ok=True)

    joblib.dump(ensemble_model, os.path.join(models_dir, 'price_forecast.pkl'))
    joblib.dump(le_category, os.path.join(models_dir, 'encoder_category.pkl'))
    joblib.dump(le_sku, os.path.join(models_dir, 'encoder_sku.pkl'))
    print(f"✅ ĐÃ ĐÚC XONG NÃO BỘ DAILY FORECAST! Lưu tại: {models_dir}")


# =====================================================================
# 2. HÀM TẢI NÃO BỘ LÊN RAM
# =====================================================================
def load_ai_model(model_dir=None):
    if model_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'models'))
    try:
        model = joblib.load(os.path.join(model_dir, 'price_forecast.pkl'))
        enc_cat = joblib.load(os.path.join(model_dir, 'encoder_category.pkl'))
        enc_sku = joblib.load(os.path.join(model_dir, 'encoder_sku.pkl'))
        return model, enc_cat, enc_sku
    except Exception as e:
        print(f"❌ Lỗi tải mô hình (Bấm train lại nhé): {e}")
        return None, None, None


# =====================================================================
# 3. HÀM DỰ BÁO THỰC CHIẾN MỖI NGÀY
# =====================================================================
def predict_future_demand(model, enc_cat, enc_sku, category_name, sku_code, target_date, current_price,
                          competitor_price, trend_score, weather_temp):
    try:
        dt = pd.to_datetime(target_date)
    except:
        dt = pd.Timestamp.now()

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

    # Phải đưa vào đúng 6 cột như lúc học
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

    # Dự báo Tổng Cầu MỖI NGÀY
    base_daily_demand = model.predict(X_new)[0]

    # --- LUẬT KINH DOANH (Áp dụng cho số bán hàng ngày) ---
    multiplier = 1.0

    if is_new_sku: multiplier *= 1.3

    if current_price > competitor_price:
        multiplier *= 0.7  # Đắt hơn -> Giảm 30% khách trong ngày
    elif current_price < competitor_price:
        multiplier *= 1.4  # Rẻ hơn -> Tăng 40% khách trong ngày

    if trend_score >= 8:
        multiplier *= (1 + (trend_score * 0.15))  # Đang trend -> Cầu ngày tăng mạnh

    # Logic thời tiết
    if weather_temp < 20 and ("áo khoác" in str(category_name).lower() or "áo len" in str(category_name).lower()):
        multiplier *= 2.0  # Lạnh rét -> Chốt đơn áo ấm gấp đôi
    elif weather_temp > 28 and ("áo khoác" in str(category_name).lower() or "áo len" in str(category_name).lower()):
        multiplier *= 0.2  # Nóng -> Bán ế áo ấm

    final_daily_demand = base_daily_demand * multiplier

    # Mức bán mỗi ngày thường rơi vào tầm vài chục cái (tùy mã hàng)
    return max(0, int(final_daily_demand))


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 🚨 SẾP MỞ KHÓA 2 DÒNG NÀY RỒI CHẠY 1 LẦN ĐỂ NÓ ĐÚC LẠI NÃO NHÉ!
    duong_dan_csv = os.path.abspath(os.path.join(current_dir, '..', '..', 'data', 'raw', 'scanner_data.csv'))
    train_model(duong_dan_csv)

    # Test thử
    model_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'models'))
    ai_model, encoder_cat, encoder_sku = load_ai_model(model_dir)
    if ai_model:
        so_ban_ngay = predict_future_demand(ai_model, encoder_cat, encoder_sku, "Áo thun nam", "N8U1", "2026-03-18",
                                            150000, 180000, 8, 28)
        print(f"✅ Test thử: Số bán ra MỖI NGÀY là {so_ban_ngay} cái!")