#!/usr/bin/env python3
"""CLI 错误类型与退出码注册表。

退出码语义（单一注册表，代码、帮助和 schema 共用）：

| 退出码 | 类别 | Agent 决策 |
| --- | --- | --- |
| 0 | 成功，包含声明的空操作 | 继续 |
| 1 | 内部错误 | 停止，收集已脱敏的诊断信息 |
| 2 | 参数或用法错误 | 修正参数，不做退避 |
| 3 | 缺少依赖或资源 | 按 next_actions 处理 |
| 4 | 超时、限流、服务暂不可用 | 按 retry_after_ms 有界退避 |
| 130 | 被中断 | 停止 |
"""

from typing import Any, Dict, List, Optional


EXIT_SUCCESS = 0
EXIT_INTERNAL = 1
EXIT_USAGE = 2
EXIT_UNAVAILABLE = 3
EXIT_TRANSIENT = 4
EXIT_INTERRUPTED = 130

# 错误码 -> (退出码, 默认可重试, 给 Agent 的下一步)
ERROR_REGISTRY: Dict[str, Dict[str, Any]] = {
    "INVALID_ARGUMENT": {
        "exit_code": EXIT_USAGE,
        "retryable": False,
        "next_actions": [{"command": "union-search --help"}],
    },
    "UNKNOWN_COMMAND": {
        "exit_code": EXIT_USAGE,
        "retryable": False,
        "next_actions": [{"command": "union-search --help"}],
    },
    "UNKNOWN_PLATFORM": {
        "exit_code": EXIT_USAGE,
        "retryable": False,
        "next_actions": [{"command": "union-search list --type platforms"}],
    },
    "UNKNOWN_GROUP": {
        "exit_code": EXIT_USAGE,
        "retryable": False,
        "next_actions": [{"command": "union-search list --type groups"}],
    },
    "MISSING_DEPENDENCY": {
        "exit_code": EXIT_UNAVAILABLE,
        "retryable": False,
        "next_actions": [{"command": "union-search doctor"}],
    },
    "PLATFORM_FAILURE": {
        "exit_code": EXIT_TRANSIENT,
        "retryable": True,
        "next_actions": [],
    },
    "PARTIAL_FAILURE": {
        "exit_code": EXIT_TRANSIENT,
        "retryable": True,
        "next_actions": [],
    },
    "DOWNLOAD_FAILURE": {
        "exit_code": EXIT_TRANSIENT,
        "retryable": True,
        "next_actions": [],
    },
    "TIMEOUT": {
        "exit_code": EXIT_TRANSIENT,
        "retryable": True,
        "next_actions": [],
    },
    "INTERNAL_ERROR": {
        "exit_code": EXIT_INTERNAL,
        "retryable": False,
        "next_actions": [],
    },
    "INTERRUPTED": {
        "exit_code": EXIT_INTERRUPTED,
        "retryable": False,
        "next_actions": [],
    },
}


class CliError(Exception):
    """带稳定错误码的 CLI 错误。"""

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        next_actions: Optional[List[Dict[str, str]]] = None,
        retry_after_ms: Optional[int] = None,
    ):
        super().__init__(message)
        spec = ERROR_REGISTRY.get(code, ERROR_REGISTRY["INTERNAL_ERROR"])
        self.code = code if code in ERROR_REGISTRY else "INTERNAL_ERROR"
        self.message = message
        self.exit_code = spec["exit_code"]
        self.retryable = spec["retryable"]
        self.details = details or {}
        self.next_actions = next_actions if next_actions is not None else list(spec["next_actions"])
        self.retry_after_ms = retry_after_ms

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "outcome": "not_started",
            "details": self.details,
            "next_actions": self.next_actions,
        }
        if self.retry_after_ms is not None:
            payload["retry_after_ms"] = self.retry_after_ms
        return payload


class CliRuntimeError(CliError):
    """运行期错误，默认为内部错误，可指定更精确的错误码。"""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(code=code, message=message, details=details)


class CliUsageError(CliError):
    """参数或用法错误。"""

    def __init__(self, message: str, code: str = "INVALID_ARGUMENT", details: Optional[Dict[str, Any]] = None):
        super().__init__(code=code, message=message, details=details)
