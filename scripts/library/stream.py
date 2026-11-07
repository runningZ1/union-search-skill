from datetime import datetime, timedelta, timezone

from library import tasks
from library.archive import upsert_document

# 收集截止 = 搜索整批时限 + 余量；CLI 异常退出没能结束收集时，执行器到点后自行结束
COLLECT_MARGIN = timedelta(seconds=120)


class FetchStream:
    """搜索开始时创建抓取任务并启动执行器；每个渠道返回后立即把它的结果加入任务，不等其他渠道。
    搜索归档完成后补齐全部资料、关联搜索运行并结束收集。"""

    def __init__(self, conn, config, options, search_timeout):
        self.conn = conn
        self.config = config
        collect_until = datetime.now(timezone.utc) + timedelta(seconds=search_timeout) + COLLECT_MARGIN
        self.task_id = tasks.create_task(conn, None, "all", {"all": True}, [], options, collect_until=collect_until)
        self.worker = tasks.launch_worker(config, self.task_id)
        self.closed = False

    def add_channel(self, platform, result):
        if not result.get("success") or not result.get("items"):
            return
        with self.conn.transaction():
            document_ids = [upsert_document(self.conn, item, platform) for item in result["items"]]
            tasks.append_items(self.conn, self.task_id, document_ids)

    def finish(self, search_id, document_ids):
        """补齐归档后的全部资料并结束收集，确认执行器已接管后返回任务摘要。"""
        with self.conn.transaction():
            tasks.append_items(self.conn, self.task_id, document_ids)
            self.conn.execute("UPDATE fetch_tasks SET search_id = %s, collect_until = NULL WHERE id = %s", (search_id, self.task_id))
        self.closed = True
        executor = tasks.wait_worker(self.conn, self.task_id, *self.worker)
        summary = tasks.summarize(self.conn, self.task_id, include_items=False)
        summary["executor"] = executor
        return summary

    def abort(self):
        """搜索或归档没有完成：结束收集并取消任务，已完成的抓取结果保留。"""
        if self.closed:
            return
        self.closed = True
        with self.conn.transaction():
            self.conn.execute("UPDATE fetch_tasks SET collect_until = NULL WHERE id = %s", (self.task_id,))
        tasks.request_cancel(self.conn, self.task_id)
