"""Flask 通用安全项：请求体大小、会话签名密钥、CSRF、可选限流。"""

from __future__ import annotations

import os

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect


def init_security(app: Flask, *, testing: bool) -> Limiter:
    app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH", "524288"))
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-insecure-change-me")
    disable_csrf = os.environ.get("FLASK_DISABLE_CSRF") == "1"
    # 始终挂载 CSRFProtect，便于模板里 csrf_token()；校验由 WTF_CSRF_ENABLED 控制
    app.config["WTF_CSRF_ENABLED"] = (not testing) and (not disable_csrf)
    CSRFProtect(app)
    enabled = (not testing) and os.environ.get("FLASK_DISABLE_RATELIMIT") != "1"
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[],
        storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
        enabled=enabled,
    )
    limiter.init_app(app)
    return limiter
