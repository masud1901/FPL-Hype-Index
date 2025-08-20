"""
Main data processing orchestrator for the FPL Data Collection System.
"""
import time
from typing import Dict, Any, List, Optional
from utils.logger import ProcessorLogger, get_logger
from .data_cleaner import DataCleaner
from .data_validator import DataValidator
from .data_enricher import DataEnricher


class DataProcessor:
    """Main data processing orchestrator."""
    
    def __init__(self):
        """Initialize the data processor with its components."""
        self.logger = ProcessorLogger("main_processor")
        self.cleaner = DataCleaner()
        self.validator = DataValidator()
        self.enricher = DataEnricher()
        
        # Performance tracking
        self.processing_stats = {
            'total_processed': 0,
            'total_cleaned': 0,
            'total_validated': 0,
            'total_enriched': 0,
            'total_failed': 0
        }
    
    async def process_scraped_data(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Process data from any scraper through the complete ETL pipeline.
        
        Args:
            data: Raw scraped data
            source: Source identifier (e.g., 'fpl_api', 'understat')
            
        Returns:
            Processed and enriched data
            
        Raises:
            ValueError: If data validation fails
        """
        start_time = time.time()
        
        try:
            self.logger.log_processing_start(
                data_count=self._count_data_records(data),
                source=source
            )
            
            # Step 1: Clean the data
            cleaned_data = await self.cleaner.clean(data, source)
            self.processing_stats['total_cleaned'] += 1
            
            # Step 2: Validate the data
            validation_result = await self.validator.validate(cleaned_data, source)
            if not validation_result['is_valid']:
                self.logger.log_processing_error(
                    ValueError(f"Data validation failed for {source}: {validation_result['issues']}")
                )
                self.processing_stats['total_failed'] += 1
                raise ValueError(f"Data validation failed for {source}: {validation_result['issues']}")
            
            self.processing_stats['total_validated'] += 1
            
            # Step 3: Enrich with additional context
            enriched_data = await self.enricher.enrich(cleaned_data, source)
            self.processing_stats['total_enriched'] += 1
            
            # Step 4: Update processing statistics
            self.processing_stats['total_processed'] += 1
            
            duration = time.time() - start_time
            self.logger.log_processing_success(
                processed_count=self._count_data_records(enriched_data),
                duration=duration
            )
            
            return enriched_data
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_processing_error(e)
            self.processing_stats['total_failed'] += 1
            raise
    
    def _count_data_records(self, data: Dict[str, Any]) -> int:
        """Count the number of records in the data.
        
        Args:
            data: Data dictionary
            
        Returns:
            Number of records
        """
        if not isinstance(data, dict):
            return 1
        
        # Count players if present
        players_count = len(data.get('players', []))
        
        # Count teams if present
        teams_count = len(data.get('teams', []))
        
        # Count gameweeks if present
        gameweeks_count = len(data.get('gameweeks', []))
        
        # Count stats if present
        stats_count = len(data.get('stats', []))
        
        total = players_count + teams_count + gameweeks_count + stats_count
        
        # If no structured data found, count as 1 record
        return total if total > 0 else 1
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'total_processed': self.processing_stats['total_processed'],
            'total_cleaned': self.processing_stats['total_cleaned'],
            'total_validated': self.processing_stats['total_validated'],
            'total_enriched': self.processing_stats['total_enriched'],
            'total_failed': self.processing_stats['total_failed'],
            'success_rate': (
                self.processing_stats['total_processed'] / 
                (self.processing_stats['total_processed'] + self.processing_stats['total_failed'])
                if (self.processing_stats['total_processed'] + self.processing_stats['total_failed']) > 0
                else 0.0
            )
        }
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.processing_stats = {
            'total_processed': 0,
            'total_cleaned': 0,
            'total_validated': 0,
            'total_enriched': 0,
            'total_failed': 0
        }
        self.logger.logger.info("Processing statistics reset") 