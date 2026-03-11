
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'Fashion_AI_Market')
BEGIN
    CREATE DATABASE Fashion_AI_Market;
END
GO

USE Fashion_AI_Market;
GO
-- TẠO CÁC BẢNG (Chuẩn hóa BCNF)

-- 1. Bảng Calendar_Context 
-- Lưu các thông tin thị trường chung theo từng ngày
IF OBJECT_ID('dbo.Calendar_Context', 'U') IS NULL
BEGIN
    CREATE TABLE Calendar_Context (
        RecordDate DATE PRIMARY KEY,
        AvgTemperature FLOAT, -- Nhiệt độ trung bình ngày hôm đó
        IsHoliday BIT DEFAULT 0 -- 1: Ngày lễ, 0: Ngày thường
    );
END

-- 2. Bảng Categories (Danh mục sản phẩm)
IF OBJECT_ID('dbo.Categories', 'U') IS NULL
BEGIN
    CREATE TABLE Categories (
        CategoryID INT PRIMARY KEY IDENTITY(1,1),
        CategoryName NVARCHAR(100) NOT NULL UNIQUE
    );
END

-- 3. Bảng Product_Models (Thông tin Mẫu mã chung - Tránh lặp lại tên/giá gốc)
-- Ví dụ: Áo thun Polo mã POLO-01
IF OBJECT_ID('dbo.Product_Models', 'U') IS NULL
BEGIN
    CREATE TABLE Product_Models (
        ModelID INT PRIMARY KEY IDENTITY(1,1),
        ModelCode VARCHAR(50) NOT NULL UNIQUE,
        ModelName NVARCHAR(255) NOT NULL,
        CategoryID INT FOREIGN KEY REFERENCES Categories(CategoryID),
        BasePrice DECIMAL(18, 2) NOT NULL
    );
END

-- 4. Bảng Product_Variants (Các biến thể cụ thể: Size, Màu - SKU thực tế)
-- Ví dụ: Áo thun Polo màu Trắng Size M
IF OBJECT_ID('dbo.Product_Variants', 'U') IS NULL
BEGIN
    CREATE TABLE Product_Variants (
        VariantID INT PRIMARY KEY IDENTITY(1,1),
        ModelID INT FOREIGN KEY REFERENCES Product_Models(ModelID),
        Color NVARCHAR(50) NOT NULL, 
        Size VARCHAR(10) NOT NULL, 
        CurrentStock INT DEFAULT 0,
        CONSTRAINT UQ_Variant UNIQUE (ModelID, Color, Size) -- Chống nhập trùng loại
    );
END

-- 5. Bảng Market_Trends (Động thái đối thủ theo Mẫu mã và Ngày)
IF OBJECT_ID('dbo.Market_Trends', 'U') IS NULL
BEGIN
    CREATE TABLE Market_Trends (
        ModelID INT FOREIGN KEY REFERENCES Product_Models(ModelID),
        RecordDate DATE FOREIGN KEY REFERENCES Calendar_Context(RecordDate),
        CompetitorAvgPrice DECIMAL(18, 2), 
        MarketTrendScore INT, -- Điểm hot trend (0-100)
        PRIMARY KEY (ModelID, RecordDate) -- Khóa chính kép
    );
END

-- 6. Bảng Internal_Sales (Lịch sử bán hàng thực tế theo từng biến thể SKU)
IF OBJECT_ID('dbo.Internal_Sales', 'U') IS NULL
BEGIN
    CREATE TABLE Internal_Sales (
        SaleID INT PRIMARY KEY IDENTITY(1,1),
        VariantID INT FOREIGN KEY REFERENCES Product_Variants(VariantID),
        SaleDate DATE FOREIGN KEY REFERENCES Calendar_Context(RecordDate),
        QuantitySold INT NOT NULL, 
        ActualSellingPrice DECIMAL(18, 2) NOT NULL
    );
END

-- 7. Bảng AI_Forecast_Results (Kết quả AI trả về lưu vào đây)
IF OBJECT_ID('dbo.AI_Forecast_Results', 'U') IS NULL
BEGIN
    CREATE TABLE AI_Forecast_Results (
        ForecastID INT PRIMARY KEY IDENTITY(1,1),
        VariantID INT FOREIGN KEY REFERENCES Product_Variants(VariantID),
        TargetDate DATE NOT NULL, -- Ngày tương lai
        PredictedMarketDemand INT, -- AI đoán sẽ bán được bao nhiêu
        SuggestedRestock INT, -- Gợi ý nhập thêm kho
        SuggestedPrice DECIMAL(18, 2), -- Giá AI gợi ý
        CreatedAt DATETIME DEFAULT GETDATE()
    );
END
GO
-- 8. Bảng Employees (Lưu trữ tài khoản đăng nhập)
IF OBJECT_ID('dbo.Employees', 'U') IS NULL
BEGIN
    CREATE TABLE Employees (
        EmployeeID INT PRIMARY KEY IDENTITY(1,1),
        Username VARCHAR(50) NOT NULL UNIQUE, -- Tên đăng nhập không được trùng
        PasswordHash VARCHAR(255) NOT NULL, -- Mật khẩu (Thực tế nên mã hóa, nhưng đồ án demo tạm lưu chuỗi)
        FullName NVARCHAR(100) NOT NULL, -- Tên hiển thị trên góc phải Dashboard
        Role VARCHAR(20) NOT NULL CHECK (Role IN ('Admin', 'Staff')), -- Chỉ cho phép 2 quyền
        IsActive BIT DEFAULT 1, -- 1: Tài khoản đang hoạt động, 0: Đã khóa/Nghỉ việc
        CreatedAt DATETIME DEFAULT GETDATE()
    );
END
GO
