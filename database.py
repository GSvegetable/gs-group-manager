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
    
    # 创建 groups 表（如果不存在）
    cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            group_id BIGINT PRIMARY KEY,
            welcome_text TEXT,
            welcome_photo_id TEXT,
            admin_ids TEXT DEFAULT '[]',
            verified BOOLEAN DEFAULT FALSE
        )
    """)
    
    # 【关键】确保 verified 列存在（处理旧版本表）
    try:
        cur.execute("""
            ALTER TABLE groups 
            ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE
        """)
    except Exception as e:
        print(f"⚠️ 添加 verified 列失败: {e}")
    
    # 创建广告触发词表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS triggers (
            id SERIAL PRIMARY KEY,
            group_id BIGINT,
            word TEXT
        )
    """)
    
    # 创建定时任务表
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
    print("✅ 数据库初始化完成")

def get_verified_status(group_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT verified FROM groups WHERE group_id = %s", (group_id,))
        row = cur.fetchone()
        if row:
            return row[0]
    except Exception as e:
        print(f"❌ 查询 verified 状态失败: {e}")
    finally:
        cur.close()
        conn.close()
    return False

def set_verified_status(group_id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO groups (group_id, verified) 
            VALUES (%s, %s) 
            ON CONFLICT (group_id) 
            DO UPDATE SET verified = excluded.verified
        """, (group_id, status))
        conn.commit()
    except Exception as e:
        print(f"❌ 设置 verified 状态失败: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
