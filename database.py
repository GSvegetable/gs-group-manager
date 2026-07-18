import os
import psycopg2
from psycopg2 import pool
import json

DATABASE_URL = os.getenv("DATABASE_URL")

db_pool = None
if DATABASE_URL:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=DATABASE_URL)

def get_db_connection():
    return db_pool.getconn() if db_pool else psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # 1. 创建 groups 表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            group_id BIGINT PRIMARY KEY,
            welcome_text TEXT,
            welcome_photo_id TEXT,
            admin_ids TEXT DEFAULT '[]'
        )
    """)
    
    # ===== ✨ 致命修复点：如果表里缺了 verified 列，立刻加上 =====
    cur.execute("""
        ALTER TABLE groups 
        ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE;
    """)
    # ============================================================

    # 2. 创建广告触发词表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS triggers (
            id SERIAL PRIMARY KEY,
            group_id BIGINT,
            word TEXT
        )
    """)
    # 3. 创建定时任务表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            group_id BIGINT,
            task_hour INT,
            message_text TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# ===== 新增：获取和设置群组验证状态 =====
def get_verified_status(group_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT verified FROM groups WHERE group_id = %s", (group_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    return False

def set_verified_status(group_id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO groups (group_id, verified) 
        VALUES (%s, %s) 
        ON CONFLICT (group_id) 
        DO UPDATE SET verified = excluded.verified
    """, (group_id, status))
    conn.commit()
    cur.close()
    conn.close()
