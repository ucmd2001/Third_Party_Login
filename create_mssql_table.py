import pyodbc


def create_database_and_table():
    # 連接到 SQL Server (調整連接字串以符合您的環境設定)
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost\\SQLEXPRESS;" 
        "DATABASE=master;"
        "Trusted_Connection=yes;"
    )

    cursor = conn.cursor()

    # 建立新資料庫
    cursor.execute(
        "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'testing') "
        "BEGIN CREATE DATABASE testing END"
    )
    conn.commit()

    # 切換到新建立的資料庫
    cursor.execute("USE testing")

    # 建立新資料表
    cursor.execute(
        "IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Account') "
        "BEGIN CREATE TABLE Account (AccountId INT PRIMARY KEY IDENTITY(1,1), "
        "Username NVARCHAR(50) NOT NULL, Password NVARCHAR(50) NOT NULL) END"
    )
    conn.commit()

    # 關閉連接
    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_database_and_table()
