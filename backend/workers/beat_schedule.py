from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    "calendar-analysis-evening": {
        "task": "workers.tasks.calendar_analysis.run",
        "schedule": crontab(hour=20, minute=0),
    },
    "pattern-analysis-weekly": {
        "task": "workers.tasks.pattern_analysis.run",
        "schedule": crontab(day_of_week=1, hour=3, minute=0),  # maandag 03:00
    },
    "memory-summarizer-monthly": {
        "task": "workers.tasks.memory_summarizer.monthly_memory_summarizer",
        "schedule": crontab(day_of_month=1, hour=2, minute=0),
    },
    "notification-sender-morning": {
        "task": "workers.tasks.notification_sender.send_morning_reminders",
        "schedule": crontab(hour=7, minute=30),
    },
    "notification-sender-evening": {
        "task": "workers.tasks.notification_sender.send_evening_reminders",
        "schedule": crontab(hour=20, minute=0),
    },
    "daycare-briefing": {
        "task": "workers.tasks.daycare_briefing.send_briefings",
        "schedule": crontab(hour=6, minute=45),
    },
    "notification-response-tracker": {
        "task": "workers.tasks.notification_sender.update_response_rates",
        "schedule": crontab(hour=4, minute=0),
    },
    "smartthings-device-sync": {
        "task": "workers.tasks.smartthings_sync.sync_all",
        "schedule": crontab(minute="*/5"),
    },
    "picknick-order-sync-daily": {
        "task": "workers.tasks.picknick_sync.sync_orders",
        "schedule": crontab(hour=8, minute=0),
    },
}
