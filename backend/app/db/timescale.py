# backend/app/db/timescale.py

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ..config import settings
from .models import Base

logger = logging.getLogger(__name__)

class TimescaleManager:
    """
    Manages TimescaleDB connection and hypertable creation.
    """

    def __init__(self):
        self.database_url = settings.DATABASE_URL
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=10
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_db(self):
        """
        Creates tables and converts them to hypertables if TimescaleDB extension is active.
        """
        logger.info("Initializing Database Tables...")

        # 1. Create standard tables
        Base.metadata.create_all(bind=self.engine)

        # 2. Convert to hypertables
        # We use raw SQL for this as SQLAlchemy doesn't natively support TimescaleDB DDL

        hypertables = [
            ('option_chain_snapshots', 'time'),
            ('stock_metrics', 'time'),
            ('structure_detections', 'time'),
            ('smart_money_verdicts', 'time'),
            ('oi_velocity_log', 'time'),
        ]

        with self.engine.connect() as conn:
            # Enable timescaledb extension if not exists
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
                conn.commit()
            except Exception as e:
                logger.warning(f"Could not enable TimescaleDB extension (might need superuser): {e}")
                logger.warning("Proceeding with standard PostgreSQL tables.")
                return

            for table, time_col in hypertables:
                try:
                    # Check if already hypertable
                    query = text(f"SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = '{table}';")
                    result = conn.execute(query).fetchone()

                    if not result:
                        logger.info(f"Converting {table} to hypertable...")
                        conn.execute(text(f"SELECT create_hypertable('{table}', '{time_col}', if_not_exists => TRUE);"))
                        conn.commit()
                except Exception as e:
                    logger.error(f"Failed to convert {table} to hypertable: {e}")
                    # Don't raise, fallback to standard table

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

db_manager = TimescaleManager()
