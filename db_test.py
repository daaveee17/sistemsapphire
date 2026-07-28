import pymysql
try:
    conn = pymysql.connect(host='localhost', port=3307, user='root', password='')
    cursor = conn.cursor()
    cursor.execute('CREATE DATABASE IF NOT EXISTS sapphire_db')
    conn.close()
    print("Database sapphire_db is ready on port 3307!")
except Exception as e:
    print('MySQL Connection Error:', e)
