"""
Database connection and session management.
"""
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from config.settings import config
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self.sync_engine = None
        self.async_engine = None
        self.sync_session_factory = None
        self.async_session_factory = None
    
    def initialize(self):
        """Initialize database engines and session factories."""
        try:
            # Create sync engine
            self.sync_engine = create_engine(
                config.database.connection_string,
                echo=config.debug,
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            # Create async engine
            self.async_engine = create_async_engine(
                config.database.async_connection_string,
                echo=config.debug,
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            # Create session factories
            self.sync_session_factory = sessionmaker(
                bind=self.sync_engine,
                autocommit=False,
                autoflush=False
            )
            
            self.async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False
            )
            
            logger.info("Database engines and session factories initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise
    
    def get_sync_session(self):
        """Get a synchronous database session."""
        if not self.sync_session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self.sync_session_factory()
        try:
            return session
        except Exception as e:
            session.close()
            logger.error("Failed to create sync session", error=str(e))
            raise
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an asynchronous database session."""
        if not self.async_session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error("Failed to create async session", error=str(e))
                raise
            finally:
                await session.close()
    
    def create_tables(self):
        """Create all database tables."""
        try:
            from .models import Base
            Base.metadata.create_all(bind=self.sync_engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        try:
            from .models import Base
            Base.metadata.drop_all(bind=self.sync_engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error("Failed to drop database tables", error=str(e))
            raise
    
    def close(self):
        """Close database connections."""
        if self.sync_engine:
            self.sync_engine.dispose()
        if self.async_engine:
            self.async_engine.dispose()
        logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager() 