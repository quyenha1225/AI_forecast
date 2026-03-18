IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'Fashion_AI_Market')
BEGIN
    CREATE DATABASE Fashion_AI_Market;
END
GO
USE Fashion_AI_Market;
GO
-- PHẦN 1:  (LOOKUP TABLES) - Khử rác dữ liệu

-- 1.  Crawler
IF OBJECT_ID('dbo.Platforms', 'U') IS NULL
CREATE TABLE Platforms (
    PlatformID INT PRIMARY KEY IDENTITY(1,1),
    PlatformName VARCHAR(50) NOT NULL UNIQUE -- Lấy giá trị: Shopee, TikTok, Lazada...
);

-- 2. Phân quyền
IF OBJECT_ID('dbo.Roles', 'U') IS NULL
CREATE TABLE Roles (
    RoleID INT PRIMARY KEY IDENTITY(1,1),
    RoleName VARCHAR(20) NOT NULL UNIQUE -- Lấy giá trị: Admin, Staff, Manager
);

-- 3. color
IF OBJECT_ID('dbo.Colors', 'U') IS NULL
CREATE TABLE Colors (
    ColorID INT PRIMARY KEY IDENTITY(1,1),
    ColorName NVARCHAR(50) NOT NULL UNIQUE
);

-- 4. size
IF OBJECT_ID('dbo.Sizes', 'U') IS NULL
CREATE TABLE Sizes (
    SizeID INT PRIMARY KEY IDENTITY(1,1),
    SizeCode VARCHAR(10) NOT NULL UNIQUE -- Lấy giá trị: S, M, L, XL, FreeSize
);

-- PHẦN 2: main data (MASTER DATA)
IF OBJECT_ID('dbo.Calendar_Context', 'U') IS NULL
CREATE TABLE Calendar_Context (
    RecordDate DATE PRIMARY KEY,
    AvgTemperature FLOAT,
    IsHoliday BIT DEFAULT 0
);

IF OBJECT_ID('dbo.Categories', 'U') IS NULL
CREATE TABLE Categories (
    CategoryID INT PRIMARY KEY IDENTITY(1,1),
    CategoryName NVARCHAR(100) NOT NULL UNIQUE
);

IF OBJECT_ID('dbo.Product_Models', 'U') IS NULL
CREATE TABLE Product_Models (
    ModelID INT PRIMARY KEY IDENTITY(1,1),
    ModelCode VARCHAR(50) NOT NULL UNIQUE,
    ModelName NVARCHAR(255) NOT NULL,
    CategoryID INT FOREIGN KEY REFERENCES Categories(CategoryID),
    BasePrice DECIMAL(18, 2) NOT NULL
);

-- Bảng SKU Biến thể (Đã bóc tách Tồn Kho và dùng ID Màu/Size)
IF OBJECT_ID('dbo.Product_Variants', 'U') IS NULL
CREATE TABLE Product_Variants (
    VariantID INT PRIMARY KEY IDENTITY(1,1),
    ModelID INT FOREIGN KEY REFERENCES Product_Models(ModelID),
    ColorID INT FOREIGN KEY REFERENCES Colors(ColorID),
    SizeID INT FOREIGN KEY REFERENCES Sizes(SizeID),
    CONSTRAINT UQ_Variant UNIQUE (ModelID, ColorID, SizeID)
);

-- Nhân viên (Đã dùng RoleID thay vì Text)
IF OBJECT_ID('dbo.Employees', 'U') IS NULL
CREATE TABLE Employees (
    EmployeeID INT PRIMARY KEY IDENTITY(1,1),
    Username VARCHAR(50) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    FullName NVARCHAR(100) NOT NULL,
    RoleID INT FOREIGN KEY REFERENCES Roles(RoleID),
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- PHẦN 3: KHỐI DỮ LIỆU ĐỘNG & GIAO DỊCH (TRANSACTIONAL DATA)

IF OBJECT_ID('dbo.Inventory_Stock', 'U') IS NULL
CREATE TABLE Inventory_Stock (
    VariantID INT PRIMARY KEY FOREIGN KEY REFERENCES Product_Variants(VariantID),
    CurrentStock INT NOT NULL DEFAULT 0,
    LastUpdated DATETIME DEFAULT GETDATE()
);

IF OBJECT_ID('dbo.Market_Trends', 'U') IS NULL
CREATE TABLE Market_Trends (
    ModelID INT FOREIGN KEY REFERENCES Product_Models(ModelID),
    RecordDate DATE FOREIGN KEY REFERENCES Calendar_Context(RecordDate),
    CompetitorAvgPrice DECIMAL(18, 2),
    MarketTrendScore INT,
    PRIMARY KEY (ModelID, RecordDate)
);

-- Trạm trung chuyển Crawler (Dùng PlatformID, chuẩn hóa cực gọn)
IF OBJECT_ID('dbo.Crawler_Raw_Data', 'U') IS NULL
CREATE TABLE Crawler_Raw_Data (
    CrawlID INT PRIMARY KEY IDENTITY(1,1),
    RecordDate DATE FOREIGN KEY REFERENCES Calendar_Context(RecordDate),
    PlatformID INT FOREIGN KEY REFERENCES Platforms(PlatformID), 
    CompetitorProductName NVARCHAR(500) NOT NULL,
    ScrapedPrice DECIMAL(18, 2) NOT NULL,
    ProductURL VARCHAR(MAX),
    MatchedModelID INT FOREIGN KEY REFERENCES Product_Models(ModelID) NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);

IF OBJECT_ID('dbo.Internal_Sales', 'U') IS NULL
CREATE TABLE Internal_Sales (
    SaleID INT PRIMARY KEY IDENTITY(1,1),
    VariantID INT FOREIGN KEY REFERENCES Product_Variants(VariantID),
    SaleDate DATE FOREIGN KEY REFERENCES Calendar_Context(RecordDate),
    QuantitySold INT NOT NULL,
    ActualSellingPrice DECIMAL(18, 2) NOT NULL,
    CONSTRAINT UQ_DailySale UNIQUE (VariantID, SaleDate) -- Chống lưu trùng 2 lần 1 ngày
);

IF OBJECT_ID('dbo.AI_Forecast_Results', 'U') IS NULL
CREATE TABLE AI_Forecast_Results (
    ForecastID INT PRIMARY KEY IDENTITY(1,1),
    VariantID INT FOREIGN KEY REFERENCES Product_Variants(VariantID),
    TargetDate DATE NOT NULL,
    PredictedMarketDemand INT,
    SuggestedRestock INT,
    SuggestedPrice DECIMAL(18, 2),
    CreatedAt DATETIME DEFAULT GETDATE()
);
GO
USE Fashion_AI_Market;
GO

-- =================================================================
-- 🧹 BƯỚC 1: TỔNG VỆ SINH DỮ LIỆU CŨ (Tránh lỗi trùng lặp)
-- =================================================================
DELETE FROM AI_Forecast_Results;
DELETE FROM Internal_Sales;
DELETE FROM Crawler_Raw_Data;
DELETE FROM Market_Trends;
DELETE FROM Inventory_Stock;
DELETE FROM Product_Variants;
DELETE FROM Product_Models;
DELETE FROM Categories;
DELETE FROM Colors;
DELETE FROM Sizes;
DELETE FROM Calendar_Context;

-- Reset lại các cột ID tự tăng (IDENTITY) về 0
DBCC CHECKIDENT ('Product_Variants', RESEED, 0);
DBCC CHECKIDENT ('Product_Models', RESEED, 0);
DBCC CHECKIDENT ('Categories', RESEED, 0);
DBCC CHECKIDENT ('Colors', RESEED, 0);
DBCC CHECKIDENT ('Sizes', RESEED, 0);
GO

-- =================================================================
-- 🚀 BƯỚC 2: BƠM DỮ LIỆU CHUẨN BCNF (Dành cho Dashboard V2.0)
-- =================================================================
USE Fashion_AI_Market;
GO

-- =================================================================
-- 🧹 BƯỚC 1: XÓA SẠCH SẼ CÁC BẢNG CŨ BỊ XUNG ĐỘT
-- =================================================================
DROP TABLE IF EXISTS AI_Forecast_Results;
DROP TABLE IF EXISTS Internal_Sales;
DROP TABLE IF EXISTS Crawler_Raw_Data;
DROP TABLE IF EXISTS Market_Trends;
DROP TABLE IF EXISTS Inventory_Stock;
DROP TABLE IF EXISTS Product_Variants;
DROP TABLE IF EXISTS Product_Models;
DROP TABLE IF EXISTS Categories;
DROP TABLE IF EXISTS Calendar_Context;
DROP TABLE IF EXISTS Employees;
DROP TABLE IF EXISTS Roles;
DROP TABLE IF EXISTS Colors;
DROP TABLE IF EXISTS Sizes;
DROP TABLE IF EXISTS Platforms;
GO

-- =================================================================
-- 🏗️ BƯỚC 2: TẠO LẠI CẤU TRÚC KHỚP 100% VỚI FILE PYTHON
-- =================================================================
CREATE TABLE Calendar_Context (RecordDate DATE PRIMARY KEY, AvgTemperature FLOAT, IsHoliday BIT DEFAULT 0);
CREATE TABLE Categories (CategoryID INT PRIMARY KEY IDENTITY(1,1), CategoryName NVARCHAR(100) NOT NULL UNIQUE);
CREATE TABLE Product_Models (ModelID INT PRIMARY KEY IDENTITY(1,1), ModelCode VARCHAR(50) NOT NULL UNIQUE, ModelName NVARCHAR(255) NOT NULL, CategoryID INT FOREIGN KEY REFERENCES Categories(CategoryID), BasePrice DECIMAL(18, 2) NOT NULL);
CREATE TABLE Product_Variants (VariantID INT PRIMARY KEY IDENTITY(1,1), ModelID INT FOREIGN KEY REFERENCES Product_Models(ModelID), Color NVARCHAR(50) NOT NULL, Size VARCHAR(10) NOT NULL, CONSTRAINT UQ_Variant UNIQUE (ModelID, Color, Size));
CREATE TABLE Inventory_Stock (VariantID INT PRIMARY KEY FOREIGN KEY REFERENCES Product_Variants(VariantID), CurrentStock INT NOT NULL DEFAULT 0, LastUpdated DATETIME DEFAULT GETDATE());
CREATE TABLE Market_Trends (ModelID INT FOREIGN KEY REFERENCES Product_Models(ModelID), RecordDate DATE FOREIGN KEY REFERENCES Calendar_Context(RecordDate), CompetitorAvgPrice DECIMAL(18, 2), MarketTrendScore INT, PRIMARY KEY (ModelID, RecordDate));
CREATE TABLE Internal_Sales (SaleID INT PRIMARY KEY IDENTITY(1,1), VariantID INT FOREIGN KEY REFERENCES Product_Variants(VariantID), SaleDate DATE FOREIGN KEY REFERENCES Calendar_Context(RecordDate), QuantitySold INT NOT NULL, ActualSellingPrice DECIMAL(18, 2) NOT NULL);
CREATE TABLE AI_Forecast_Results (ForecastID INT PRIMARY KEY IDENTITY(1,1), VariantID INT FOREIGN KEY REFERENCES Product_Variants(VariantID), TargetDate DATE NOT NULL, PredictedMarketDemand INT, SuggestedRestock INT, SuggestedPrice DECIMAL(18, 2), CreatedAt DATETIME DEFAULT GETDATE());
CREATE TABLE Employees (EmployeeID INT PRIMARY KEY IDENTITY(1,1), Username VARCHAR(50) NOT NULL UNIQUE, PasswordHash VARCHAR(255) NOT NULL, FullName NVARCHAR(100) NOT NULL, Role VARCHAR(20) NOT NULL CHECK (Role IN ('Admin', 'Staff')), IsActive BIT DEFAULT 1, CreatedAt DATETIME DEFAULT GETDATE());
GO

-- =================================================================
-- 🚀 BƯỚC 3: BƠM KỊCH BẢN DỮ LIỆU ĐỂ TEST BIỂU ĐỒ AI
-- =================================================================
INSERT INTO Employees (Username, PasswordHash, FullName, Role) VALUES ('admin', '123456', N'Hà Văn Võ Quyền', 'Admin');

INSERT INTO Calendar_Context (RecordDate, AvgTemperature, IsHoliday) VALUES 
('2026-03-11', 25.5, 0), ('2026-03-12', 26.0, 0), ('2026-03-13', 24.5, 0),
('2026-03-14', 23.0, 1), ('2026-03-15', 22.5, 1), ('2026-03-16', 25.0, 0), ('2026-03-17', 26.5, 0);

INSERT INTO Categories (CategoryName) VALUES (N'Áo Khoác'), (N'Áo Thun'), (N'Quần Jean');

DECLARE @CatAK INT = (SELECT CategoryID FROM Categories WHERE CategoryName = N'Áo Khoác');
DECLARE @CatAT INT = (SELECT CategoryID FROM Categories WHERE CategoryName = N'Áo Thun');
DECLARE @CatQJ INT = (SELECT CategoryID FROM Categories WHERE CategoryName = N'Quần Jean');

INSERT INTO Product_Models (ModelCode, ModelName, CategoryID, BasePrice) VALUES 
('AK-01', N'Áo Khoác Bomber Trượt Nước', @CatAK, 450000),
('AT-01', N'Áo Thun Polo Lạnh', @CatAT, 150000),
('QJ-01', N'Quần Jean Nam Rách Gối', @CatQJ, 350000);

DECLARE @ModAK INT = (SELECT ModelID FROM Product_Models WHERE ModelCode = 'AK-01');
DECLARE @ModAT INT = (SELECT ModelID FROM Product_Models WHERE ModelCode = 'AT-01');
DECLARE @ModQJ INT = (SELECT ModelID FROM Product_Models WHERE ModelCode = 'QJ-01');

INSERT INTO Product_Variants (ModelID, Color, Size) VALUES 
(@ModAK, N'Đen', 'L'), (@ModAT, N'Trắng', 'M'), (@ModQJ, N'Xanh Denim', '32');

DECLARE @VarAK INT = (SELECT VariantID FROM Product_Variants WHERE ModelID = @ModAK);
DECLARE @VarAT INT = (SELECT VariantID FROM Product_Variants WHERE ModelID = @ModAT);
DECLARE @VarQJ INT = (SELECT VariantID FROM Product_Variants WHERE ModelID = @ModQJ);

INSERT INTO Inventory_Stock (VariantID, CurrentStock, LastUpdated) VALUES 
(@VarAK, 85, GETDATE()), (@VarAT, 120, GETDATE()), (@VarQJ, 10, GETDATE());

INSERT INTO Market_Trends (ModelID, RecordDate, CompetitorAvgPrice, MarketTrendScore) VALUES 
(@ModAK, '2026-03-17', 430000, 8), (@ModAT, '2026-03-17', 160000, 5), (@ModQJ, '2026-03-17', 340000, 9); 

INSERT INTO Internal_Sales (VariantID, SaleDate, QuantitySold, ActualSellingPrice) VALUES 
(@VarAK, '2026-03-11', 15, 450000), (@VarAT, '2026-03-11', 25, 150000),
(@VarAK, '2026-03-12', 12, 450000), (@VarAT, '2026-03-12', 20, 150000),
(@VarAK, '2026-03-13', 18, 450000), (@VarAT, '2026-03-13', 30, 150000),
(@VarAK, '2026-03-14', 35, 420000), (@VarAT, '2026-03-14', 50, 140000), 
(@VarAK, '2026-03-15', 40, 420000), (@VarAT, '2026-03-15', 55, 140000),
(@VarAK, '2026-03-16', 10, 450000), (@VarAT, '2026-03-16', 22, 150000),
(@VarAK, '2026-03-17', 14, 450000), (@VarAT, '2026-03-17', 28, 150000),
(@VarQJ, '2026-03-17', 5, 350000);  

INSERT INTO AI_Forecast_Results (VariantID, TargetDate, PredictedMarketDemand, SuggestedRestock) VALUES 
(@VarAK, '2026-03-11', 14, 0), (@VarAT, '2026-03-11', 22, 0),
(@VarAK, '2026-03-12', 13, 0), (@VarAT, '2026-03-12', 25, 0),
(@VarAK, '2026-03-13', 15, 0), (@VarAT, '2026-03-13', 28, 0),
(@VarAK, '2026-03-14', 30, 10),(@VarAT, '2026-03-14', 45, 0), 
(@VarAK, '2026-03-15', 38, 0), (@VarAT, '2026-03-15', 50, 0),
(@VarAK, '2026-03-16', 12, 0), (@VarAT, '2026-03-16', 20, 0),
(@VarAK, '2026-03-17', 15, 0), (@VarAT, '2026-03-17', 30, 0),
(@VarQJ, '2026-03-17', 45, 35); 

PRINT N'✅ ĐÃ KHÔI PHỤC VÀ BƠM DỮ LIỆU THÀNH CÔNG!';
GO