"""
搜索日志记录器模块
用于记录统一搜索的详细日志信息
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class SearchLogger:
    """搜索日志记录器"""

    def __init__(self, verbose: bool = False):
        """
        初始化搜索日志记录器

        Args:
            verbose: 是否启用详细日志模式
        """
        self.verbose = verbose
        self.log_dir = Path(__file__).parent / "search_logs"
        self.log_dir.mkdir(exist_ok=True)

    def log_union_search(
        self,
        query: str,
        results: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        记录统一搜索日志

        Args:
            query: 搜索关键词
            results: 搜索结果列表
            metadata: 额外的元数据信息

        Returns:
            日志文件路径
        """
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c for c in query if c.isalnum() or c in (" ", "-", "_")).strip()[:20].replace(" ", "_")
        filename = f"search_{safe_query}_{timestamp}.json"
        filepath = self.log_dir / filename

        # 构建日志数据
        log_data = {
            "keyword": query,
            "timestamp": datetime.now().isoformat(),
            "results": results,
        }

        # 添加元数据
        if metadata:
            log_data["metadata"] = metadata

        # 如果是详细模式，添加更多详细信息
        if self.verbose:
            log_data["verbose_info"] = {
                "platform_details": metadata.get("platform_details", []) if metadata else [],
                "response_times": metadata.get("response_times", {}) if metadata else {},
            }

        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

        return str(filepath)
