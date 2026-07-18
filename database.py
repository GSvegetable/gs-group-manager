import os
import psycopg2
from psycopg2 import pool
import json

DATABASE_URL = os.getenv('DATABASE_URL')

# 创建数据库连接池
db_pool = None
if DATABASE_URL:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=DATABASE_URL)

def get_db_connection():
    return db_pool.getconn() if db_pool else psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # 创建群组配置表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            group_id BIGINT PRIMARY KEY,
            welcome_text TEXT,
            welcome_photo_id TEXT,
            admin_ids TEXT DEFAULT '[]'
        )
    """)
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
    # 创建群组授权表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS authorized_groups (
            group_id BIGINT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
