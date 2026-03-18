import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, VotingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import os


def evaluate_ai_model_extreme(csv_file_path):
    print("⏳ Đang kích hoạt buồng máy ENSEMBLE LEARNING (Lai giữa RF và GB)...")
    df = pd.read_csv(csv_file_path)

    # =================================================================
    # 1. KỸ THUẬT ĐẶC TRƯNG NGẦM (FEATURE ENGINEERING)
    # =================================================================
    df_clean = df.copy()
    df_clean['Unit_Price'] = df_clean['Sales_Amount'] / df_clean['Quantity']
    df_clean['Date'] = pd.to_datetime(df_clean['Date'], dayfirst=True, errors='coerce')
    df_clean = df_clean.dropna(subset=['Date'])
    df_clean['Month'] = df_clean['Date'].dt.month
    df_clean['Day'] = df_clean['Date'].dt.day
    df_clean['DayOfWeek'] = df_clean['Date'].dt.dayofweek
    df_clean['Is_Weekend'] = (df_clean['DayOfWeek'] >= 5).astype(int)

    columns_to_drop = ['Unnamed: 0', 'Customer_ID', 'Transaction_ID', 'Sales_Amount', 'Date']
    df_clean = df_clean.drop(columns=[c for c in columns_to_drop if c in df_clean.columns])

    le_category = LabelEncoder()
    df_clean['SKU_Category'] = le_category.fit_transform(df_clean['SKU_Category'].astype(str))
    le_sku = LabelEncoder()
    df_clean['SKU'] = le_sku.fit_transform(df_clean['SKU'].astype(str))
    df_clean = df_clean.dropna()

    X = df_clean.drop(columns=['Quantity'])
    y = df_clean['Quantity']

    # =================================================================
    # 2. CHIA TẬP DỮ LIỆU (TRAIN 80% - TEST 20%)
    # =================================================================
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    print(f"📊 Dữ liệu đã chia: Train ({len(X_train)}), Test ({len(X_test)})")
    print(f"🧬 Các giác quan AI đang dùng để học: {X.columns.tolist()}")

    # =================================================================
    # 3. HUẤN LUYỆN BẰNG ENSEMBLE LEARNING (HỢP BÍCH)
    # =================================================================
    print("\n🧠 AI đang học bài bằng thuật toán Ensemble...")
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    gb = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, random_state=42)

    # Gộp 2 thằng lại
    model = VotingRegressor(estimators=[('RF', rf), ('GB', gb)])
    model.fit(X_train, y_train)

    print("📝 Đang chấm điểm...")
    y_test_pred = model.predict(X_test)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_r2 = r2_score(y_test, y_test_pred)

    # =================================================================
    # 4. TRẢ KẾT QUẢ CHO LEADER
    # =================================================================
    print("\n" + "=" * 60)
    print("🚀 BẢNG ĐIỂM CỦA AI ENSEMBLE (CỖ MÁY LAI)")
    print("=" * 60)
    print(f"📍 TẬP TEST (Thi Thật):")
    print(f"   - Sai số trung bình (MAE): {test_mae:.4f} sản phẩm")
    print(f"   - R2 Score: {test_r2:.4f}")

    print("\n🔍 SOI BÀI THI THẬT (Thực tế vs AI Dự báo):")
    test_results = pd.DataFrame({'Thực_Tế': y_test, 'AI_Dự_Báo': y_test_pred.round()})
    print(test_results.sample(5))


# =====================================================================
# CHẠY THỬ
# =====================================================================
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    duong_dan_csv = os.path.join(current_dir, "../../data/raw/scanner_data.csv")
    evaluate_ai_model_extreme(duong_dan_csv)