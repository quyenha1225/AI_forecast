import pandas as pd
import joblib
import os
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, VotingRegressor


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

    # 1.3 Song kiếm hợp bích
    print("🤖 Đang truyền nội công cho 2 thuật toán...")
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    gb = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, random_state=42)

    ensemble_model = VotingRegressor(estimators=[('RF', rf), ('GB', gb)])
    ensemble_model.fit(X, y)

    # 1.4 Xuất file Não bộ
    os.makedirs('../models', exist_ok=True)
    joblib.dump(ensemble_model, '../models/price_forecast.pkl')
    joblib.dump(le_category, '../models/encoder_category.pkl')
    joblib.dump(le_sku, '../models/encoder_sku.pkl')
    print("✅ ĐÃ ĐÚC XONG NÃO BỘ LAI (ENSEMBLE)! Sẵn sàng chinh chiến.")


# =====================================================================
# 2. HÀM TẢI NÃO BỘ LÊN RAM
# =====================================================================
def load_ai_model(model_dir="../models"):
    try:
        model = joblib.load(os.path.join(model_dir, 'price_forecast.pkl'))
        enc_cat = joblib.load(os.path.join(model_dir, 'encoder_category.pkl'))
        enc_sku = joblib.load(os.path.join(model_dir, 'encoder_sku.pkl'))
        return model, enc_cat, enc_sku
    except Exception as e:
        print(f"❌ Lỗi tải mô hình: {e}")
        return None, None, None


# =====================================================================
# 3. HÀM DỰ BÁO THỰC CHIẾN (Áp dụng Bộ Luật Kinh Doanh)
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

        # Đưa đúng 7 giác quan vào cho AI đoán
    X_new = pd.DataFrame({
        'SKU_Category': [cat_encoded],
        'SKU': [sku_encoded],
        'Unit_Price': [current_price],
        'Month': [dt.month],
        'Day': [dt.day],
        'DayOfWeek': [dt.weekday()],
        'Is_Weekend': [1 if dt.weekday() >= 5 else 0]
    })

    # Lấy dự báo từ Cỗ Máy Lai
    final_demand = model.predict(X_new)[0]

    # --- LUẬT KINH DOANH CỦA LEADER QUYỀN ---
    if is_new_sku:
        final_demand *= 1.2  # Hàng mới tăng 20%
    if current_price > competitor_price:
        final_demand *= 0.85  # Bán đắt hơn đối thủ mất 15% khách
    if trend_score >= 8:
        final_demand *= 1.3  # Hot trend tăng 30%
    if weather_temp < 20 and str(category_name) == "07":
        final_demand *= 1.5  # Lạnh bán áo ấm tốt
    elif weather_temp > 30 and str(category_name) == "07":
        final_demand *= 0.5  # Nóng ế áo ấm

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
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 🚨 BƯỚC 1: MỞ KHÓA DÒNG NÀY 1 LẦN ĐỂ ĐÚC LẠI NÃO BỘ LAI
    # duong_dan_csv = os.path.join(current_dir, "../../data/raw/scanner_data.csv")
    # train_model(duong_dan_csv)

    # BƯỚC 2: CHẠY THỬ DỰ BÁO
    model_dir = os.path.join(current_dir, "../../models")
    ai_model, encoder_cat, encoder_sku = load_ai_model(model_dir)

    if ai_model:
        ma_hang = "CZUZX"
        loai_hang = "0H2"
        ngay = "2026-04-05"

        so_ban_du_kien = predict_future_demand(
            ai_model, encoder_cat, encoder_sku,
            loai_hang, ma_hang, ngay,
            current_price=6.35, competitor_price=6.00,
            trend_score=9, weather_temp=25
        )
        so_can_nhap = calculate_restock_amount(so_ban_du_kien, current_stock=0)

        print("\n🏆 KẾT QUẢ TỪ HỆ THỐNG ENSEMBLE AI:")
        print(f"👉 Nhu cầu thị trường (Sau khi áp Luật kinh doanh): {so_ban_du_kien} sản phẩm")
        print(f"🚛 LỆNH XUẤT KHO: Cần nhập {so_can_nhap} sản phẩm!")