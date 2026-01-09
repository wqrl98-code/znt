# -*- coding: utf-8 -*-
"""
持久化存储管理器 (Persistence Manager) - 优化修复版
功能：
1. KnowledgeKeeper: 文件指纹与分析结果缓存（秒级启动）
2. TaskQueue: SQLite任务持久化队列（崩溃恢复 + 单例模式）
"""
import os
import json
import time
import sqlite3
import uuid
import threading
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# 配置日志
logger = logging.getLogger("PersistenceManager")


# ==========================================
# 1. 任务队列数据库 (单例模式，线程安全)
# ==========================================

class TaskQueue:
    """基于SQLite的任务持久化队列，确保任务不丢失"""

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """单例模式实现，确保全局只有一个任务队列实例"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskQueue, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: str = None):
        """初始化任务队列"""
        if self._initialized:
            return

        if not db_path:
            # 默认存在 Database/tasks.db
            base_dir = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE', 'Database')
            if not os.path.exists(base_dir):
                try:
                    os.makedirs(base_dir, exist_ok=True)
                    logger.info(f"📁 创建数据库目录: {base_dir}")
                except Exception as e:
                    logger.error(f"❌ 创建数据库目录失败: {e}")
                    raise
            db_path = os.path.join(base_dir, 'tasks.db')

        self.db_path = db_path
        self._init_db()
        self.lock = threading.RLock()
        self._initialized = True
        logger.info(f"✅ [TaskQueue] 初始化完成，数据库路径: {self.db_path}")

    def _init_db(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                cursor = conn.cursor()
                # 创建任务表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        payload TEXT,
                        result TEXT,
                        created_at REAL,
                        updated_at REAL,
                        retry_count INTEGER DEFAULT 0,
                        error_message TEXT
                    )
                ''')
                # 创建索引以提高查询性能
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON tasks(created_at)')
                conn.commit()
                logger.info("✅ [TaskQueue] 数据库表结构初始化完成")
        except Exception as e:
            logger.error(f"❌ [TaskQueue] 数据库初始化失败: {e}")
            raise

    def add_task(self, task_type: str, payload: Dict[str, Any]) -> str:
        """添加新任务，返回 task_id"""
        task_id = str(uuid.uuid4())
        now = time.time()

        try:
            payload_json = json.dumps(payload, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ JSON序列化失败: {e}")
            payload_json = "{}"

        with self.lock:
            try:
                with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                    conn.execute(
                        "INSERT INTO tasks (task_id, task_type, status, payload, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (task_id, task_type, "PENDING", payload_json, now, now)
                    )
                logger.debug(f"📝 [TaskQueue] 添加任务: {task_type} - {task_id}")
            except Exception as e:
                logger.error(f"❌ 写入任务失败: {e}")
                raise
        return task_id

    def update_status(self, task_id: str, status: str, result: Dict = None, error_message: str = None):
        """更新任务状态"""
        now = time.time()
        result_json = None
        if result:
            try:
                result_json = json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logger.warning(f"⚠️ 结果序列化失败: {e}")
                result_json = json.dumps({"error": "结果序列化失败"})

        with self.lock:
            try:
                with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                    if result_json:
                        conn.execute(
                            "UPDATE tasks SET status = ?, result = ?, updated_at = ?, error_message = ? WHERE task_id = ?",
                            (status, result_json, now, error_message, task_id)
                        )
                    else:
                        conn.execute(
                            "UPDATE tasks SET status = ?, updated_at = ?, error_message = ? WHERE task_id = ?",
                            (status, now, error_message, task_id)
                        )
                logger.debug(f"📝 [TaskQueue] 更新任务状态: {task_id} -> {status}")
            except Exception as e:
                logger.error(f"❌ 更新任务状态失败: {e}")

    def get_task(self, task_id: str) -> Optional[Dict]:
        """根据task_id获取任务详情"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
                    row = cursor.fetchone()

                    if row:
                        task = {
                            "task_id": row["task_id"],
                            "task_type": row["task_type"],
                            "status": row["status"],
                            "payload": json.loads(row["payload"]) if row["payload"] else {},
                            "result": json.loads(row["result"]) if row["result"] else None,
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"],
                            "retry_count": row["retry_count"],
                            "error_message": row["error_message"]
                        }
                        return task
            except Exception as e:
                logger.error(f"❌ 获取任务失败: {e}")
            return None

    def get_pending_tasks(self) -> List[Dict]:
        """获取未完成的任务 (用于启动时恢复)"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM tasks WHERE status IN ('PENDING', 'RUNNING') ORDER BY created_at ASC")
                    rows = cursor.fetchall()

                    tasks = []
                    for row in rows:
                        try:
                            payload = json.loads(row["payload"]) if row["payload"] else {}
                        except:
                            payload = {}

                        tasks.append({
                            "task_id": row["task_id"],
                            "task_type": row["task_type"],
                            "payload": payload,
                            "created_at": row["created_at"],
                            "status": row["status"]
                        })
                    return tasks
            except Exception as e:
                logger.error(f"❌ 获取待处理任务失败: {e}")
                return []

    def get_all_tasks(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取所有任务（分页查询）"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ? OFFSET ?",
                        (limit, offset)
                    )
                    rows = cursor.fetchall()

                    tasks = []
                    for row in rows:
                        try:
                            payload = json.loads(row["payload"]) if row["payload"] else {}
                        except:
                            payload = {}

                        try:
                            result = json.loads(row["result"]) if row["result"] else None
                        except:
                            result = None

                        tasks.append({
                            "task_id": row["task_id"],
                            "task_type": row["task_type"],
                            "status": row["status"],
                            "payload": payload,
                            "result": result,
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"],
                            "retry_count": row["retry_count"]
                        })
                    return tasks
            except Exception as e:
                logger.error(f"❌ 获取所有任务失败: {e}")
                return []

    def clear_completed_tasks(self, days_to_keep: int = 7):
        """清理过期的已完成任务"""
        cutoff = time.time() - (days_to_keep * 86400)
        with self.lock:
            try:
                with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM tasks WHERE status IN ('COMPLETED', 'FAILED') AND updated_at < ?",
                        (cutoff,)
                    )
                    deleted_count = cursor.rowcount
                    conn.commit()
                    logger.info(f"🧹 [TaskQueue] 清理了 {deleted_count} 个过期任务")
            except Exception as e:
                logger.error(f"❌ 清理任务失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取任务队列统计信息"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                    cursor = conn.cursor()

                    # 统计各状态任务数量
                    cursor.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
                    status_counts = {row[0]: row[1] for row in cursor.fetchall()}

                    # 统计任务类型分布
                    cursor.execute("SELECT task_type, COUNT(*) as count FROM tasks GROUP BY task_type")
                    type_counts = {row[0]: row[1] for row in cursor.fetchall()}

                    # 获取最旧和最新任务时间
                    cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM tasks")
                    min_max = cursor.fetchone()

                    return {
                        "total_tasks": sum(status_counts.values()),
                        "status_counts": status_counts,
                        "type_counts": type_counts,
                        "oldest_task": min_max[0] if min_max and min_max[0] else None,
                        "newest_task": min_max[1] if min_max and min_max[1] else None,
                        "db_path": self.db_path
                    }
            except Exception as e:
                logger.error(f"❌ 获取统计信息失败: {e}")
                return {}


# ==========================================
# 2. 知识缓存管理器
# ==========================================

class KnowledgeKeeper:
    """知识缓存管理器，实现文件增量更新和秒级启动"""

    def __init__(self, io_manager):
        self.io_manager = io_manager
        self.cache_data = {}  # 内存中的缓存
        self.current_persona = "Default"
        self.cache_file_path = ""
        self._lock = threading.RLock()

    def load_persona_cache(self, persona_name: str):
        """加载特定人格的知识缓存"""
        self.current_persona = persona_name

        # 缓存文件存放在: Inputs/{Persona}/.knowledge_index.json
        # 前面加个点，作为隐藏文件，不被当做普通文档读取
        if hasattr(self.io_manager, 'get_persona_folder'):
            persona_dir = self.io_manager.get_persona_folder(persona_name)
        else:
            # 兼容旧版本
            persona_dir = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE', 'Inputs', persona_name)

        # 确保目录存在
        if not os.path.exists(persona_dir):
            logger.warning(f"⚠️ [Cache] 人格目录不存在: {persona_dir}")
            return

        self.cache_file_path = os.path.join(persona_dir, ".knowledge_index.json")

        if os.path.exists(self.cache_file_path):
            try:
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    with self._lock:
                        self.cache_data = json.load(f)
                logger.info(f"✅ [Cache] 已加载 {persona_name} 的知识索引，包含 {len(self.cache_data)} 条记录")
            except json.JSONDecodeError as e:
                logger.error(f"❌ [Cache] 索引文件JSON格式错误，将重建: {e}")
                self.cache_data = {}
                # 备份损坏的文件
                backup_path = self.cache_file_path + f".backup.{int(time.time())}"
                os.rename(self.cache_file_path, backup_path)
                logger.info(f"📁 [Cache] 已备份损坏文件至: {backup_path}")
            except Exception as e:
                logger.error(f"❌ [Cache] 加载索引失败，将重建: {e}")
                self.cache_data = {}
        else:
            logger.info(f"ℹ️ [Cache] {persona_name} 尚无索引，将建立新库")
            self.cache_data = {}

    def get_cached_record(self, file_path: str) -> Optional[Dict]:
        """
        检查文件是否有有效缓存
        返回: 缓存数据 dict 或 None
        """
        if not os.path.exists(file_path):
            return None

        filename = os.path.basename(file_path)
        current_mtime = os.path.getmtime(file_path)

        with self._lock:
            # 检查记录是否存在
            if filename in self.cache_data:
                record = self.cache_data[filename]
                # 🔥 关键：比对修改时间 (精确到小数点后4位)
                # 如果缓存里的时间 == 文件实际时间，说明没改过，直接用缓存
                cached_mtime = record.get("mtime", 0)
                if abs(cached_mtime - current_mtime) < 0.1:
                    return record

        return None  # 需要重新扫描

    def check_cache(self, file_path: str) -> Optional[Dict]:
        """
        检查文件是否已有有效缓存（兼容性别名）
        :return: 缓存记录 或 None
        """
        return self.get_cached_record(file_path)

    def update_record(self, file_path: str, result_data: Dict[str, Any]):
        """
        分析完成后，更新缓存记录
        """
        filename = os.path.basename(file_path)
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ [Cache] 文件不存在，无法更新缓存: {file_path}")
            return

        # 提取关键信息用于UI快速恢复
        record = {
            "mtime": os.path.getmtime(file_path),
            "analyzed_at": time.time(),
            "file_path": file_path,  # 保存完整路径以便追踪
            # 保存用于 UI 显示的数据
            "radar_metrics": result_data.get("radar_metrics", {}),
            "keywords": result_data.get("semantic_summary", {}).get("keywords", {}),
            "summary_text": result_data.get("text_report", "")[:500],  # 存个摘要预览
            "dna_features": result_data.get("dna_features", {}),  # 新增DNA特征存储
            # 如果需要，这里也可以存 full_text，但会导致 json 很大
            # 建议不存全文，全文检索交给 RAG/向量库
        }

        with self._lock:
            self.cache_data[filename] = record
            self._save_to_disk()

        logger.debug(f"📝 [Cache] 更新缓存记录: {filename}")

    def delete_record(self, file_path: str):
        """删除指定文件的缓存记录"""
        filename = os.path.basename(file_path)
        with self._lock:
            if filename in self.cache_data:
                del self.cache_data[filename]
                self._save_to_disk()
                logger.info(f"🗑️ [Cache] 删除缓存记录: {filename}")

    def clear_cache(self):
        """清空当前人格的缓存"""
        with self._lock:
            cache_size = len(self.cache_data)
            self.cache_data = {}
            self._save_to_disk()
            logger.info(f"🧹 [Cache] 清空了 {cache_size} 条缓存记录")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            return {
                "total_records": len(self.cache_data),
                "persona": self.current_persona,
                "cache_file": self.cache_file_path,
                "last_modified": os.path.getmtime(self.cache_file_path) if os.path.exists(
                    self.cache_file_path) else None
            }

    def _save_to_disk(self):
        """写入磁盘"""
        if not self.cache_file_path:
            return

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)

            # 写入临时文件，然后重命名，确保原子性
            temp_path = self.cache_file_path + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)

            # 替换原文件
            if os.path.exists(self.cache_file_path):
                os.remove(self.cache_file_path)
            os.rename(temp_path, self.cache_file_path)

        except Exception as e:
            logger.error(f"❌ [Cache] 保存失败: {e}")


# ==========================================
# 3. 全局管理器工厂
# ==========================================

class PersistenceManager:
    """持久化管理器工厂类，方便统一管理"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """单例模式"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(PersistenceManager, cls).__new__(cls)
            return cls._instance

    def __init__(self, io_manager=None):
        if not hasattr(self, '_initialized'):
            self.io_manager = io_manager
            self.knowledge_keeper = None
            self.task_queue = None
            self._initialized = True

            if io_manager:
                self.knowledge_keeper = KnowledgeKeeper(io_manager)

    def init_task_queue(self, db_path: str = None) -> TaskQueue:
        """初始化任务队列（按需初始化）"""
        if not self.task_queue:
            self.task_queue = TaskQueue(db_path)
        return self.task_queue

    def get_knowledge_keeper(self) -> KnowledgeKeeper:
        """获取知识缓存管理器"""
        if not self.knowledge_keeper and self.io_manager:
            self.knowledge_keeper = KnowledgeKeeper(self.io_manager)
        return self.knowledge_keeper

    def get_task_queue(self) -> TaskQueue:
        """获取任务队列"""
        if not self.task_queue:
            self.task_queue = TaskQueue()
        return self.task_queue


# ==========================================
# 🔥 核心修正：实例化并导出全局变量
# ==========================================

# 全局单例实例
GLOBAL_TASK_QUEUE = TaskQueue()
GLOBAL_PERSISTENCE_MANAGER = PersistenceManager()


def get_task_queue() -> TaskQueue:
    """获取全局任务队列实例（便捷函数）"""
    return GLOBAL_TASK_QUEUE


def get_persistence_manager(io_manager=None) -> PersistenceManager:
    """获取全局持久化管理器实例（便捷函数）"""
    if io_manager and not GLOBAL_PERSISTENCE_MANAGER.io_manager:
        GLOBAL_PERSISTENCE_MANAGER.io_manager = io_manager
    return GLOBAL_PERSISTENCE_MANAGER

