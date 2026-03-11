import sys
import os

# Đảm bảo Python nhận diện thư mục src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.frontend.ui_main import App

def main():
    print("Khởi động hệ thống Fashion AI Market...")
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()