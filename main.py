from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymysql

host = "localhost"
user = "root"
password = ""
database = "hospital"

app = FastAPI()


def ensure_database_and_table():
    # connect without specifying database to create it if needed
    conn = pymysql.connect(host=host, user=user, password=password, cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        conn.commit()
    finally:
        conn.close()

    # connect to the database and ensure table exists
    conn = pymysql.connect(host=host, user=user, password=password, database=database, cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS appointments (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  name VARCHAR(100),
                  email VARCHAR(100),
                  phone VARCHAR(20),
                  date DATE,
                  time VARCHAR(20),
                  department VARCHAR(50),
                  message TEXT
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def on_startup():
    try:
        ensure_database_and_table()
    except Exception as e:
        print("Warning: could not connect to MySQL at startup:", e)
        print("The app will still run. Start MySQL and retry requests.")


class Appointment(BaseModel):
    name: str
    email: str
    phone: str
    date: str
    time: str
    department: str
    message: str = ""


@app.post("/appointments")
def create_appointment(a: Appointment):
    conn = pymysql.connect(host=host, user=user, password=password, database=database, cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cur:
            sql = "INSERT INTO appointments (name,email,phone,date,time,department,message) VALUES (%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql, (a.name, a.email, a.phone, a.date, a.time, a.department, a.message))
            conn.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
