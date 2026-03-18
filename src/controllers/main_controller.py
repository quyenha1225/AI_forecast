import pandas as pd
from datetime import datetime
from src.backend import db_manager as db

try:
    from src.ai_core.predictor import load_ai_model, predict_future_demand
except ImportError:
    def load_ai_model(path):
        return None, None, None


    def predict_future_demand(*args, **kwargs):
        return 0


class MainController:
    def __init__(self):
        self.model = None
        self.enc_cat = None
        self.enc_sku = None

    def handle_login(self, username, password):
        return db.check_login(username, password)

    def get_dashboard_metrics(self):
        conn = db.connect_db()
        if not conn: return 0, 0, 0, pd.DataFrame()

        query = """
        WITH LatestForecast AS (
            SELECT VariantID, PredictedMarketDemand, SuggestedRestock,
                   ROW_NUMBER() OVER(PARTITION BY VariantID ORDER BY ForecastID DESC) as rn
            FROM AI_Forecast_Results
        )
        SELECT PM.ModelCode AS [Mã SKU], PM.ModelName AS [Tên Sản Phẩm],
               ISNULL(inv.CurrentStock, 0) AS [Tồn Kho], 
               ISNULL(f.PredictedMarketDemand, 0) AS [Dự Báo Ngày],
               (ISNULL(f.PredictedMarketDemand, 0) * 30) AS [Dự Báo Tháng], -- 🚀 Tính luôn tháng ở đây
               ISNULL(f.SuggestedRestock, 0) AS [Cần Nhập Thêm]
        FROM Product_Variants v
        JOIN Product_Models PM ON v.ModelID = PM.ModelID
        LEFT JOIN Inventory_Stock inv ON v.VariantID = inv.VariantID
        LEFT JOIN LatestForecast f ON v.VariantID = f.VariantID AND f.rn = 1
        """
        df = pd.read_sql(query, conn)
        conn.close()

        tong_ton = df['Tồn Kho'].sum() if not df.empty else 0
        # 🚀 SỬA TẠI ĐÂY: Thẻ Dashboard sẽ hiện TỔNG THEO THÁNG cho nó hoành tráng
        tong_du_bao_thang = df['Dự Báo Tháng'].sum() if not df.empty else 0

        df_can_nhap = df[df['Cần Nhập Thêm'] > 0].sort_values(by='Cần Nhập Thêm',
                                                              ascending=False) if not df.empty else pd.DataFrame()
        thieu_hang = len(df_can_nhap)

        return tong_ton, tong_du_bao_thang, thieu_hang, df_can_nhap
    def get_trend_chart_data(self):
        return db.get_dashboard_trend_data()

    def get_market_chart_data(self):
        return db.get_market_competitor_data()

    def get_category_structure_data(self):
        return db.get_category_structure_data()

    def get_inventory_view(self):
        return db.get_inventory()

    def get_categories(self):
        return db.get_all_categories()

    def get_full_inventory_list_for_dropdown(self):
        conn = db.connect_db()
        if not conn: return []
        query = "SELECT PV.VariantID, PM.ModelCode + ' - ' + PM.ModelName AS SKU_Name FROM Product_Variants PV JOIN Product_Models PM ON PV.ModelID = PM.ModelID"
        df = pd.read_sql(query, conn)
        conn.close()
        return df.to_dict('records')

    def update_stock_transaction(self, variant_id, quantity, is_import, base_price=0):
        if is_import:
            return db.update_stock(variant_id, quantity)
        else:
            return db.add_internal_sales(variant_id, datetime.now().strftime("%Y-%m-%d"), quantity, base_price)

    def run_real_ai_forecast(self, category_name, trend_score, temp, price_diff):
        conn = db.connect_db()
        if not conn: return pd.DataFrame()

        query = f"""
            SELECT PV.VariantID, PM.ModelCode, PM.ModelName, ISNULL(PM.BasePrice, 0) AS BasePrice, ISNULL(INV.CurrentStock, 0) as CurrentStock
            FROM Product_Variants PV
            JOIN Product_Models PM ON PV.ModelID = PM.ModelID
            JOIN Categories C ON PM.CategoryID = C.CategoryID
            LEFT JOIN Inventory_Stock INV ON PV.VariantID = INV.VariantID
            WHERE C.CategoryName = N'{category_name}'
        """
        df_products = pd.read_sql(query, conn)
        conn.close()

        if df_products.empty: return pd.DataFrame()

        if self.model is None:
            import streamlit as st
            with st.spinner("⚙️ Đang kết nối với Lõi AI Ensemble (Random Forest & Gradient Boosting)..."):
                self.model, self.enc_cat, self.enc_sku = load_ai_model("models")

        results = []
        for _, row in df_products.iterrows():
            base_price = float(row['BasePrice'])
            comp_price = base_price * (1 + price_diff / 100)

            if self.model is None:
                prediction_daily = int(row['CurrentStock'] * 0.1 + trend_score * 2)
            else:
                prediction_daily = predict_future_demand(
                    self.model, self.enc_cat, self.enc_sku,
                    category_name=category_name, sku_code=row['ModelCode'],
                    target_date=datetime.now().strftime("%Y-%m-%d"),
                    current_price=base_price, competitor_price=comp_price,
                    trend_score=trend_score, weather_temp=temp
                )

            prediction_monthly = prediction_daily * 30
            goi_y_nhap_1_cuc = max(0, prediction_monthly - row['CurrentStock'])

            results.append({
                'VariantID': row['VariantID'],
                'Mã SKU': row['ModelCode'],
                'Tên Sản Phẩm': row['ModelName'],
                'Tồn Kho Hiện Tại': row['CurrentStock'],
                'Dự Báo / Ngày': prediction_daily,
                'Dự Báo / Tháng': prediction_monthly,
                'Gợi Ý Nhập Thêm': goi_y_nhap_1_cuc
            })

        return pd.DataFrame(results)

    def save_predictions(self, df_results):
        success = True
        for _, row in df_results.iterrows():
            target_date = datetime.now().strftime("%Y-%m-%d")
            if not db.save_ai_forecast(row['VariantID'], target_date, row['Dự Báo / Ngày'], row['Gợi Ý Nhập Thêm'], 0):
                success = False
        return success