from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class AIProviderState(db.Model):
    """Track state of AI providers (Groq, HuggingFace)"""
    __tablename__ = 'ai_provider_states'
    
    id = db.Column(db.Integer, primary_key=True)
    provider_name = db.Column(db.String(50), unique=True, nullable=False)
    is_enabled = db.Column(db.Boolean, default=True)
    is_healthy = db.Column(db.Boolean, default=True)
    last_health_check = db.Column(db.DateTime)
    total_requests = db.Column(db.Integer, default=0)
    successful_requests = db.Column(db.Integer, default=0)
    failed_requests = db.Column(db.Integer, default=0)
    last_error = db.Column(db.String(500))
    last_error_at = db.Column(db.DateTime)
    avg_latency_ms = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIUsageLog(db.Model):
    """Log AI API requests for analytics"""
    __tablename__ = 'ai_usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    provider = db.Column(db.String(50), nullable=False)
    operation_type = db.Column(db.String(50), nullable=False)
    model_used = db.Column(db.String(100))
    success = db.Column(db.Boolean, nullable=False)
    error_type = db.Column(db.String(100))
    error_message = db.Column(db.String(500))
    duration_seconds = db.Column(db.Float)
    latency_ms = db.Column(db.Integer)
    session_id = db.Column(db.String(100))
    cached = db.Column(db.Boolean, default=False)
    hour_bucket = db.Column(db.Integer)
    tool_name = db.Column(db.String(100))


class DailyStats(db.Model):
    """Daily aggregated statistics"""
    __tablename__ = 'daily_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, index=True)
    total_requests = db.Column(db.Integer, default=0)
    successful_requests = db.Column(db.Integer, default=0)
    failed_requests = db.Column(db.Integer, default=0)
    cached_requests = db.Column(db.Integer, default=0)
    llm_requests = db.Column(db.Integer, default=0)
    whisper_requests = db.Column(db.Integer, default=0)
    vision_requests = db.Column(db.Integer, default=0)
    groq_requests = db.Column(db.Integer, default=0)
    huggingface_requests = db.Column(db.Integer, default=0)
    unique_sessions = db.Column(db.Integer, default=0)
    page_views = db.Column(db.Integer, default=0)
    tool_usage = db.Column(db.Text)
    avg_latency_ms = db.Column(db.Float, default=0)
    peak_hour = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RequestCache(db.Model):
    """Persistent cache for AI requests"""
    __tablename__ = 'request_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    operation_type = db.Column(db.String(50), nullable=False)
    result = db.Column(db.Text, nullable=False)
    file_hash = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    access_count = db.Column(db.Integer, default=1)


class ActiveSession(db.Model):
    """Track active user sessions"""
    __tablename__ = 'active_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_id = db.Column(db.String(100))
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(500))
    device_type = db.Column(db.String(50))
    browser = db.Column(db.String(100))
    os_name = db.Column(db.String(100))
    country = db.Column(db.String(100))
    current_page = db.Column(db.String(200))
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    page_views = db.Column(db.Integer, default=1)
    ai_requests = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class SessionRateLimit(db.Model):
    """Track rate limits per session"""
    __tablename__ = 'session_rate_limits'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    request_count = db.Column(db.Integer, default=0)
    audio_count = db.Column(db.Integer, default=0)
    long_audio_count = db.Column(db.Integer, default=0)
    window_start = db.Column(db.DateTime, default=datetime.utcnow)
    last_request = db.Column(db.DateTime, default=datetime.utcnow)
    is_blocked = db.Column(db.Boolean, default=False)
    blocked_until = db.Column(db.DateTime)
    block_reason = db.Column(db.String(200))


class ActivityLog(db.Model):
    """Log all tool activities (AI and non-AI) for admin dashboard"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    session_id = db.Column(db.String(100), index=True)
    ip_address = db.Column(db.String(45))
    tool_name = db.Column(db.String(100), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    details = db.Column(db.Text)
    duration_ms = db.Column(db.Integer)
    file_size = db.Column(db.Integer)
    error_message = db.Column(db.String(500))
    user_agent = db.Column(db.String(500))
    device_type = db.Column(db.String(50))


class ToolStats(db.Model):
    """Aggregated tool usage statistics"""
    __tablename__ = 'tool_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    tool_name = db.Column(db.String(100), nullable=False, index=True)
    usage_count = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    avg_duration_ms = db.Column(db.Float, default=0)
    total_file_size = db.Column(db.BigInteger, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('date', 'tool_name', name='unique_date_tool'),
    )


class HourlyStats(db.Model):
    """Hourly statistics for charts"""
    __tablename__ = 'hourly_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    hour = db.Column(db.Integer, nullable=False)
    total_requests = db.Column(db.Integer, default=0)
    successful_requests = db.Column(db.Integer, default=0)
    failed_requests = db.Column(db.Integer, default=0)
    ai_requests = db.Column(db.Integer, default=0)
    groq_requests = db.Column(db.Integer, default=0)
    huggingface_requests = db.Column(db.Integer, default=0)
    avg_latency_ms = db.Column(db.Float, default=0)
    unique_sessions = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('date', 'hour', name='unique_date_hour'),
    )


class ErrorLog(db.Model):
    """Track all errors for debugging"""
    __tablename__ = 'error_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    error_type = db.Column(db.String(100), nullable=False, index=True)
    error_message = db.Column(db.Text, nullable=False)
    stack_trace = db.Column(db.Text)
    provider = db.Column(db.String(50))
    tool_name = db.Column(db.String(100))
    session_id = db.Column(db.String(100))
    request_data = db.Column(db.Text)
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
