import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Nhúng các tầng xử lý (Đảm bảo file run_app.py nằm đúng chỗ để import không lỗi)
from src.backend import db_manager
from src.ai_core import predictor

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Fashion AI Market - Retail Dashboard")
        # Mở rộng form ra một chút (1200x800) để lát nữa có chỗ vẽ Biểu đồ cho đẹp
        self.geometry("1200x800")

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # 1. MENU TRÁI (SIDEBAR)
        # ==========================================
        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.logo = ctk.CTkLabel(self.sidebar, text="👗 Retail - AI", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo.pack(pady=30)

        self.btn_dashboard = ctk.CTkButton(self.sidebar, text="📊 Dashboard", command=self.show_dashboard)
        self.btn_dashboard.pack(pady=10, padx=20)

        self.btn_inventory = ctk.CTkButton(self.sidebar, text="📦 Quản lý Kho", command=self.show_inventory)
        self.btn_inventory.pack(pady=10, padx=20)

        self.btn_ai = ctk.CTkButton(self.sidebar, text="🤖 Chạy Dự Báo AI", command=self.run_ai_prediction)
        self.btn_ai.pack(pady=10, padx=20)

        # (TÍNH NĂNG MỚI) Nút Xuất Báo Cáo Excel tô màu xanh nổi bật
        self.btn_export = ctk.CTkButton(self.sidebar, text="📥 Xuất Báo Cáo Excel", fg_color="#27ae60", hover_color="red", command=self.action_export_excel)
        self.btn_export.pack(pady=40, padx=20)

        # ==========================================
        # 2. MÀN HÌNH CHÍNH BÊN PHẢI (MAIN CONTENT)
        # ==========================================
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.lbl_title = ctk.CTkLabel(self.main_frame, text="Màn Hình Thống Kê & Cảnh Báo", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_title.pack(pady=10)

        # (TÍNH NĂNG MỚI) Khung chừa sẵn để nhúng Biểu đồ bằng matplotlib
        self.chart_frame = ctk.CTkFrame(self.main_frame, height=300)
        self.chart_frame.pack(fill="x", pady=10, padx=20)
        self.lbl_chart_placeholder = ctk.CTkLabel(self.chart_frame, text="[Biểu đồ cột Tồn Kho vs AI Dự Báo sẽ vẽ ở đây]", text_color="gray50")
        self.lbl_chart_placeholder.pack(pady=100)

        # Khung chừa sẵn để làm Bảng dữ liệu có Cảnh báo đỏ
        self.table_frame = ctk.CTkFrame(self.main_frame)
        self.table_frame.pack(fill="both", expand=True, pady=10, padx=20)
        self.lbl_table_placeholder = ctk.CTkLabel(self.table_frame, text="[Bảng dữ liệu hàng hóa & Cảnh báo sẽ hiển thị ở đây]", text_color="gray50")
        self.lbl_table_placeholder.pack(pady=50)

    # ==========================================
    # 3. CÁC HÀM XỬ LÝ SỰ KIỆN GIAO DIỆN
    # ==========================================
    def login_event(self):
        pass

    def show_dashboard(self):
        """Kích hoạt khi bấm nút Dashboard. Sẽ gọi hàm lấy Data, vẽ Biểu đồ và load Bảng"""
        pass

    def show_inventory(self):
        pass

    def run_ai_prediction(self):
        pass

    def draw_chart(self, data):
        """(HÀM MỚI) Gọi matplotlib vẽ biểu đồ dán vào self.chart_frame"""
        pass

    def load_table_with_warnings(self, data):
        """(HÀM MỚI) Đổ data vào bảng. Quét logic: Nếu tồn kho < dự báo -> Tô màu đỏ dòng đó"""
        pass

    def action_export_excel(self):
        """(HÀM MỚI) Kích hoạt khi bấm nút Xuất Excel, gọi hàm backend lưu file"""
        pass