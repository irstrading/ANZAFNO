from app.celery_app import celery_app
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Run fetch_market_data_task every 1 minute
    "fetch-market-data-every-minute": {
        "task": "app.tasks.fetch_market_data_task",
        "schedule": crontab(minute="*"), # Every minute
    },
    # Run process_option_chain_task for NIFTY every 3 minutes
    "process-nifty-chain-every-3-min": {
        "task": "app.tasks.process_option_chain_task",
        "schedule": crontab(minute="*/3"), # Every 3 minutes
        "args": ("NIFTY",),
    },
    # Run process_option_chain_task for BANKNIFTY every 3 minutes
    "process-banknifty-chain-every-3-min": {
        "task": "app.tasks.process_option_chain_task",
        "schedule": crontab(minute="*/3"),
        "args": ("BANKNIFTY",),
    },
}
