"""Structured logging utilities for production observability."""
import logging
import json
import time
from typing import Any, Dict, Optional
from datetime import datetime
from pythonjsonlogger import jsonlogger
import sys


class StructuredLogger:
    """Provides structured logging with JSON output and context tracking."""
    
    def __init__(self, name: str, level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()
        
        # JSON handler for structured logs
        json_handler = logging.StreamHandler(sys.stdout)
        json_handler.setFormatter(
            jsonlogger.JsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s %(extra)s')
        )
        self.logger.addHandler(json_handler)
        
        self.context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs):
        """Set context variables to include in all log messages."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all context variables."""
        self.context.clear()
    
    def _get_extra(self):
        """Get extra fields including context and timestamp."""
        extra = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            **self.context
        }
        return extra
    
    def info(self, message: str, **kwargs):
        """Log info level message with structured data."""
        extra = self._get_extra()
        extra.update(kwargs)
        self.logger.info(message, extra={'extra': extra})
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error level message with exception details."""
        extra = self._get_extra()
        extra.update(kwargs)
        if exception:
            extra['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
            }
        self.logger.error(message, extra={'extra': extra}, exc_info=exception)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message with structured data."""
        extra = self._get_extra()
        extra.update(kwargs)
        self.logger.warning(message, extra={'extra': extra})
    
    def debug(self, message: str, **kwargs):
        """Log debug level message with structured data."""
        extra = self._get_extra()
        extra.update(kwargs)
        self.logger.debug(message, extra={'extra': extra})
    
    def log_scan(self, scan_id: str, threat_level: str, duration: float, **kwargs):
        """Log a scan operation with metrics."""
        self.info(
            f"Scan completed: {threat_level}",
            scan_id=scan_id,
            threat_level=threat_level,
            duration_ms=int(duration * 1000),
            **kwargs
        )
    
    def log_llm_call(self, provider: str, model: str, tokens: int, duration: float, status: str = "success"):
        """Log an LLM API call with metrics."""
        self.info(
            f"LLM call: {provider}/{model}",
            provider=provider,
            model=model,
            tokens=tokens,
            duration_ms=int(duration * 1000),
            status=status
        )
    
    def log_api_request(self, method: str, path: str, status_code: int, duration: float):
        """Log an API request with metrics."""
        self.info(
            f"API request: {method} {path} -> {status_code}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=int(duration * 1000)
        )
    
    def log_database_query(self, operation: str, table: str, duration: float, rows_affected: int = 0):
        """Log a database query with metrics."""
        self.debug(
            f"Database query: {operation} on {table}",
            operation=operation,
            table=table,
            duration_ms=int(duration * 1000),
            rows_affected=rows_affected
        )


def get_structured_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger instance."""
    return StructuredLogger(name)
