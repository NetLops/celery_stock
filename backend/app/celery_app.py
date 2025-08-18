from celery import Celery
import os

# Redis配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 创建Celery应用
celery_app = Celery(
    "stock_analysis",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    task_soft_time_limit=25 * 60,  # 25分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    'update-market-data': {
        'task': 'app.tasks.update_market_data',
        'schedule': 300.0,  # 每5分钟执行一次
    },
    'cleanup-expired-analysis': {
        'task': 'app.tasks.cleanup_expired_analysis',
        'schedule': 3600.0,  # 每小时执行一次
    },
}