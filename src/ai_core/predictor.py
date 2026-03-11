import pandas as pd

def train_model(csv_file_path):
    """Đọc data Kaggle, làm sạch, huấn luyện Random Forest và xuất file .pkl"""
    pass

def load_ai_model(model_path="models/price_forecast.pkl"):
    """Tải file não bộ AI lên RAM để chuẩn bị dự báo"""
    pass

def predict_future_demand(product_id, target_date, current_price, competitor_price, trend_score, weather_temp):
    """
    Nhập thông số đầu vào -> AI nhả ra số lượng bán dự kiến.
    """
    pass

def calculate_restock_amount(predicted_demand, current_stock):
    """Công thức: Lượng cần nhập = Dự báo bán - Tồn kho hiện tại"""
    pass