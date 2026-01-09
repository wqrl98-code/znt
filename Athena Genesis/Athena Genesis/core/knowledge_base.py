# 文件路径: core/knowledge_base.py
# -*- coding: utf-8 -*-
import os
import json
import threading
import jieba
import re
import time
from datetime import datetime
from config.settings import SETTINGS


class KnowledgeBase:
    def __init__(self):
        # 获取知识库路径
        kb_dir = SETTINGS.PATHS.directories.get('knowledge_base')
        if not kb_dir:
            # 如果没有配置路径，使用默认路径
            kb_dir = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE', 'KnowledgeBase')

        # 确保目录存在
        if not os.path.exists(kb_dir):
            os.makedirs(kb_dir, exist_ok=True)

        # 数据库文件路径
        self.db_path = os.path.join(kb_dir, "global_index.json")

        # 内存数据结构
        self.data = {
            "documents": {},
            "metadata": {
                "total_docs": 0,
                "total_words": 0,
                "last_updated": "",
                "created_at": datetime.now().isoformat()
            }
        }

        # 🔥🔥🔥【核心修复】使用可重入锁 (RLock) 🔥🔥🔥
        # 将 Lock 改为 RLock，防止 ensure_loaded 调用 load_db 时发生死锁
        self.lock = threading.RLock()

        # 延迟加载标志
        self._loaded = False

        print(f"📚 知识库初始化完成，路径: {self.db_path}")

    def ensure_loaded(self):
        """确保数据已加载"""
        if not self._loaded:
            # 使用RLock，允许同一个线程重入
            with self.lock:
                # 双重检查，防止多个线程同时进入
                if not self._loaded:
                    print("🔍 正在加载知识库数据...")
                    self.load_db()
                    self._loaded = True
                    print(f"✅ 知识库加载完成: {len(self.data['documents'])} 个文档")

    def load_db(self):
        """加载数据库"""
        # 注意：这里不再需要with self.lock，因为ensure_loaded已经加锁
        # 而且由于是RLock，同一个线程可以重入，但这里我们不需要再次加锁
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)

                # 合并数据，保留原有结构
                if "documents" in loaded_data:
                    self.data["documents"] = loaded_data["documents"]

                # 更新元数据
                if "metadata" in loaded_data:
                    # 保留原有创建时间
                    if "created_at" in loaded_data["metadata"]:
                        self.data["metadata"]["created_at"] = loaded_data["metadata"]["created_at"]

                    # 更新统计信息
                    self.data["metadata"]["total_docs"] = len(self.data["documents"])
                    self.data["metadata"]["total_words"] = sum(
                        doc.get("length", 0) for doc in self.data["documents"].values()
                    )
                    self.data["metadata"]["last_updated"] = datetime.now().isoformat()
                else:
                    # 如果没有元数据，创建默认
                    self.data["metadata"]["total_docs"] = len(self.data["documents"])
                    self.data["metadata"]["total_words"] = sum(
                        doc.get("length", 0) for doc in self.data["documents"].values()
                    )
                    self.data["metadata"]["last_updated"] = datetime.now().isoformat()

                print(f"📖 从磁盘加载了 {len(self.data['documents'])} 个文档")
                return True
            else:
                print("📝 知识库文件不存在，创建新数据库")
                # 保存空的数据库
                self.save_db()
                return False

        except Exception as e:
            print(f"❌ 加载知识库失败: {e}")
            # 创建新的数据结构
            self.data = {
                "documents": {},
                "metadata": {
                    "total_docs": 0,
                    "total_words": 0,
                    "last_updated": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat()
                }
            }
            return False

    def save_db(self):
        """保存数据库"""
        with self.lock:  # RLock，允许同一个线程重入
            try:
                # 确保目录存在
                db_dir = os.path.dirname(self.db_path)
                if not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)

                # 更新元数据
                self.data["metadata"]["total_docs"] = len(self.data["documents"])
                self.data["metadata"]["total_words"] = sum(
                    doc.get("length", 0) for doc in self.data["documents"].values()
                )
                self.data["metadata"]["last_updated"] = datetime.now().isoformat()

                # 保存到文件
                with open(self.db_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)

                # print(f"💾 知识库已保存到: {self.db_path}")
                return True

            except Exception as e:
                print(f"❌ 保存知识库失败: {e}")
                return False

    def clear_db(self):
        """清空数据库"""
        with self.lock:
            self.data = {
                "documents": {},
                "metadata": {
                    "total_docs": 0,
                    "total_words": 0,
                    "last_updated": datetime.now().isoformat(),
                    "created_at": self.data["metadata"].get("created_at", datetime.now().isoformat())
                }
            }
            self._loaded = True  # 标记为已加载，防止再次加载
            self.save_db()
            print("🧹 [KnowledgeBase] 内存索引已清空")

    def add_document(self, filename, content, keywords, metadata=None):
        """添加文档到索引"""
        if metadata is None:
            metadata = {}

        self.ensure_loaded()

        with self.lock:
            # 检查文档是否已存在
            if filename in self.data["documents"]:
                print(f"⚠️ 文档已存在，更新: {filename}")

            # 简单的摘要生成 (取前200字)
            summary = content[:200].replace('\n', ' ') + "..."

            # 确保keywords是字典格式
            if isinstance(keywords, list):
                # 如果是列表，转换为字典（词频为1）
                keywords_dict = {kw: 1 for kw in keywords}
            elif isinstance(keywords, dict):
                keywords_dict = keywords
            else:
                keywords_dict = {}

            self.data["documents"][filename] = {
                "content": content,
                "keywords": keywords_dict,
                "summary": summary,
                "metadata": metadata,
                "length": len(content),
                "added_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # 自动保存
            self.save_db()
            print(f"📚 [KnowledgeBase] 已索引文档: {filename}")

            return True

    def search(self, query, top_k=3):
        """
        简单的关键词搜索
        返回: 拼接好的参考文本字符串
        """
        self.ensure_loaded()

        if not query or not query.strip():
            return ""

        # 分词
        query_words = set(jieba.lcut(query))
        scores = []

        # 创建数据快照，减少锁持有时间
        documents_snapshot = {}
        with self.lock:
            documents_snapshot = self.data["documents"].copy()

        for fname, doc_data in documents_snapshot.items():
            score = 0
            content = doc_data.get("content", "")
            doc_keywords = doc_data.get("keywords", {})

            # 1. 标题命中权重
            if query in fname:
                score += 10

            # 2. 关键词命中权重
            for qw in query_words:
                if qw in doc_keywords:
                    score += doc_keywords[qw]  # 加上词频
                elif qw in content:
                    score += 1

            if score > 0:
                scores.append((score, fname, doc_data))

        # 按分数排序
        scores.sort(key=lambda x: x[0], reverse=True)

        # 组装结果
        results = []
        for score, fname, doc_data in scores[:top_k]:
            snippet = doc_data.get("summary", "")
            # 如果是深度搜索，可以返回更多内容
            results.append(f"【来源: {fname} (匹配度:{score})】\n{snippet}\n")

        if not results:
            return ""  # 未找到

        return "\n".join(results)

    def get_all_docs(self):
        """获取所有文档列表"""
        self.ensure_loaded()
        with self.lock:
            return list(self.data["documents"].keys())

    def get_doc_count(self):
        """获取文档数量"""
        self.ensure_loaded()
        with self.lock:
            return len(self.data["documents"])

    def get_total_words(self):
        """获取总字数"""
        self.ensure_loaded()
        with self.lock:
            return self.data["metadata"].get("total_words", 0)

    def remove_document(self, filename):
        """移除文档"""
        self.ensure_loaded()
        with self.lock:
            if filename in self.data["documents"]:
                del self.data["documents"][filename]
                self.save_db()
                print(f"🗑️ [KnowledgeBase] 已移除文档: {filename}")
                return True
            return False

    def get_document(self, filename):
        """获取特定文档"""
        self.ensure_loaded()
        with self.lock:
            return self.data["documents"].get(filename)

    def update_document(self, filename, content=None, keywords=None, metadata=None):
        """更新文档"""
        self.ensure_loaded()
        with self.lock:
            if filename in self.data["documents"]:
                doc = self.data["documents"][filename]

                if content is not None:
                    doc["content"] = content
                    doc["length"] = len(content)
                    # 更新摘要
                    doc["summary"] = content[:200].replace('\n', ' ') + "..."

                if keywords is not None:
                    if isinstance(keywords, list):
                        doc["keywords"] = {kw: 1 for kw in keywords}
                    elif isinstance(keywords, dict):
                        doc["keywords"] = keywords

                if metadata is not None:
                    doc["metadata"].update(metadata)

                doc["updated_at"] = datetime.now().isoformat()

                self.save_db()
                print(f"🔄 [KnowledgeBase] 已更新文档: {filename}")
                return True
            return False

    def get_stats(self):
        """获取统计信息"""
        self.ensure_loaded()
        with self.lock:
            return {
                "total_documents": len(self.data["documents"]),
                "total_words": self.data["metadata"].get("total_words", 0),
                "last_updated": self.data["metadata"].get("last_updated", ""),
                "created_at": self.data["metadata"].get("created_at", ""),
                "db_path": self.db_path
            }

    def backup(self, backup_path=None):
        """备份知识库"""
        self.ensure_loaded()
        with self.lock:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, f"knowledge_backup_{timestamp}.json")

            try:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                print(f"💾 知识库已备份到: {backup_path}")
                return True
            except Exception as e:
                print(f"❌ 备份失败: {e}")
                return False

    def restore_from_backup(self, backup_path):
        """从备份恢复"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            with self.lock:
                self.data = backup_data
                self._loaded = True
                self.save_db()

            print(f"♻️ 已从备份恢复: {backup_path}")
            return True

        except Exception as e:
            print(f"❌ 恢复失败: {e}")
            return False
