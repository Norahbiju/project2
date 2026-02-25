from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

# Database configuration comes from environment variables (see .env or environment)
# Required/expected vars: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, optional DB_PORT
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else None
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "hospital")

app = FastAPI()


def get_connection(database: str | None = None):
    kwargs = {
        "host": DB_HOST,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "cursorclass": pymysql.cursors.DictCursor,
    }
    if DB_PORT:
        kwargs["port"] = DB_PORT
    if database:
        kwargs["database"] = database
    return pymysql.connect(**kwargs)


def ensure_database_and_table():
    # connect without specifying database to create it if needed
    conn = get_connection(database=None)
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.commit()
    finally:
        conn.close()

    # connect to the database and ensure table exists
    conn = get_connection(database=DB_NAME)
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
    conn = get_connection(database=DB_NAME)
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
