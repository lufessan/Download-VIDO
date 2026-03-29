"""
AI Providers Abstraction Layer
Unified interface for multiple AI providers with smart routing and caching.

Supported Providers:
- Groq: LLM (Llama) + Whisper (Audio Transcription)
- HuggingFace: Vision models (Image Analysis)

Features:
- Provider abstraction for easy swapping
- Smart caching to reduce API calls
- Rate limiting per user
- Comprehensive logging and analytics
"""

import os
import time
import hashlib
import logging
import threading
import base64
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Dict, Any, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Base exception for AI provider errors"""
    pass


class RateLimitError(AIProviderError):
    """Rate limit exceeded"""
    pass


class QuotaExhaustedError(AIProviderError):
    """Provider quota exhausted"""
    pass


class ProviderNotConfiguredError(AIProviderError):
    """Provider API key not configured"""
    pass


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
    
    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is available"""
        pass


class GroqProvider(AIProvider):
    """
    Groq API Provider for:
    - LLM text generation (Llama models)
    - Audio transcription (Whisper)
    """
    
    BASE_URL = "https://api.groq.com/openai/v1"
    DEFAULT_LLM_MODEL = "llama-3.3-70b-versatile"
    DEFAULT_WHISPER_MODEL = "whisper-large-v3"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self._lock = threading.Lock()
    
    @property
    def name(self) -> str:
        return "groq"
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def health_check(self) -> bool:
        if not self.is_configured:
            return False
        try:
            response = requests.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(
        self,
        prompt: str,
        system_prompt: str = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        Call Groq LLM for text generation.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use (default: llama-3.3-70b-versatile)
            temperature: Response temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
        """
        if not self.is_configured:
            raise ProviderNotConfiguredError(
                "مفتاح Groq API غير مُعد. يرجى إضافة GROQ_API_KEY في الإعدادات."
            )
        
        model = model or os.environ.get("GROQ_LLM_MODEL", self.DEFAULT_LLM_MODEL)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=120
            )
            
            if response.status_code == 429:
                raise RateLimitError("تم تجاوز حد الطلبات لـ Groq. يرجى المحاولة لاحقاً.")
            
            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                logger.error(f"[Groq] API Error: {error_msg}")
                raise AIProviderError(f"خطأ في Groq API: {error_msg}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.Timeout:
            raise AIProviderError("انتهت مهلة الاتصال بـ Groq. يرجى المحاولة مرة أخرى.")
        except requests.exceptions.RequestException as e:
            logger.error(f"[Groq] Request error: {e}")
            raise AIProviderError(f"خطأ في الاتصال بـ Groq: {str(e)[:100]}")
    
    def transcribe_audio(
        self,
        audio_path: str,
        language: str = None,
        model: str = None
    ) -> str:
        """
        Transcribe audio using Groq Whisper.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'ar', 'en')
            model: Whisper model to use
            
        Returns:
            Transcribed text
        """
        if not self.is_configured:
            raise ProviderNotConfiguredError(
                "مفتاح Groq API غير مُعد. يرجى إضافة GROQ_API_KEY في الإعدادات."
            )
        
        model = model or os.environ.get("GROQ_WHISPER_MODEL", self.DEFAULT_WHISPER_MODEL)
        
        if not os.path.exists(audio_path):
            raise AIProviderError(f"ملف الصوت غير موجود: {audio_path}")
        
        file_size = os.path.getsize(audio_path)
        max_size = 25 * 1024 * 1024
        if file_size > max_size:
            raise AIProviderError(
                f"حجم الملف الصوتي كبير جداً ({file_size / (1024*1024):.1f} MB). "
                f"الحد الأقصى هو 25 MB."
            )
        
        try:
            with open(audio_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_path), audio_file, "audio/mpeg")
                }
                data = {
                    "model": model,
                    "response_format": "text"
                }
                if language:
                    data["language"] = language
                
                response = requests.post(
                    f"{self.BASE_URL}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                    data=data,
                    timeout=300
                )
            
            if response.status_code == 429:
                raise RateLimitError("تم تجاوز حد الطلبات لـ Groq Whisper. يرجى المحاولة لاحقاً.")
            
            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                logger.error(f"[Groq Whisper] API Error: {error_msg}")
                raise AIProviderError(f"خطأ في Groq Whisper: {error_msg}")
            
            return response.text.strip()
            
        except requests.exceptions.Timeout:
            raise AIProviderError("انتهت مهلة تحويل الصوت. يرجى المحاولة بملف أقصر.")
        except requests.exceptions.RequestException as e:
            logger.error(f"[Groq Whisper] Request error: {e}")
            raise AIProviderError(f"خطأ في الاتصال بـ Groq: {str(e)[:100]}")


class HuggingFaceProvider(AIProvider):
    """
    HuggingFace Inference API Provider for:
    - Vision/Image analysis
    - Image classification
    """
    
    BASE_URL = "https://api-inference.huggingface.co/models"
    DEFAULT_VISION_MODEL = "Salesforce/blip-image-captioning-large"
    DEFAULT_VQA_MODEL = "dandelin/vilt-b32-finetuned-vqa"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("HUGGINGFACE_API_KEY")
        self._lock = threading.Lock()
    
    @property
    def name(self) -> str:
        return "huggingface"
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def health_check(self) -> bool:
        if not self.is_configured:
            return False
        try:
            response = requests.get(
                "https://huggingface.co/api/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def analyze_image(
        self,
        image_path: str,
        question: str = None,
        model: str = None,
        wait_for_model: bool = True
    ) -> str:
        """
        Analyze image using HuggingFace Vision models.
        
        Args:
            image_path: Path to image file
            question: Optional question about the image (for VQA)
            model: Model to use
            wait_for_model: Wait if model is loading
            
        Returns:
            Analysis result text
        """
        if not self.is_configured:
            raise ProviderNotConfiguredError(
                "مفتاح HuggingFace API غير مُعد. يرجى إضافة HUGGINGFACE_API_KEY في الإعدادات."
            )
        
        if not os.path.exists(image_path):
            raise AIProviderError(f"ملف الصورة غير موجود: {image_path}")
        
        if question:
            model = model or os.environ.get("HF_VQA_MODEL", self.DEFAULT_VQA_MODEL)
        else:
            model = model or os.environ.get("HF_VISION_MODEL", self.DEFAULT_VISION_MODEL)
        
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            headers = self._get_headers()
            if wait_for_model:
                headers["X-Wait-For-Model"] = "true"
            
            if question:
                image_b64 = base64.b64encode(image_data).decode("utf-8")
                payload = {
                    "inputs": {
                        "image": image_b64,
                        "question": question
                    }
                }
                response = requests.post(
                    f"{self.BASE_URL}/{model}",
                    headers={**headers, "Content-Type": "application/json"},
                    json=payload,
                    timeout=120
                )
            else:
                response = requests.post(
                    f"{self.BASE_URL}/{model}",
                    headers=headers,
                    data=image_data,
                    timeout=120
                )
            
            if response.status_code == 503:
                error_data = response.json()
                if "estimated_time" in error_data:
                    wait_time = int(error_data["estimated_time"])
                    raise AIProviderError(
                        f"النموذج قيد التحميل. يرجى المحاولة بعد {wait_time} ثانية."
                    )
                raise AIProviderError("خدمة HuggingFace غير متاحة حالياً.")
            
            if response.status_code == 429:
                raise RateLimitError("تم تجاوز حد الطلبات لـ HuggingFace. يرجى المحاولة لاحقاً.")
            
            if response.status_code != 200:
                logger.error(f"[HuggingFace] API Error: {response.text}")
                raise AIProviderError(f"خطأ في HuggingFace: {response.text[:100]}")
            
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    if "generated_text" in result[0]:
                        return result[0]["generated_text"]
                    elif "answer" in result[0]:
                        return result[0]["answer"]
                    elif "label" in result[0]:
                        return f"{result[0]['label']} ({result[0].get('score', 0):.2%})"
                return str(result[0])
            
            return str(result)
            
        except requests.exceptions.Timeout:
            raise AIProviderError("انتهت مهلة تحليل الصورة. يرجى المحاولة مرة أخرى.")
        except requests.exceptions.RequestException as e:
            logger.error(f"[HuggingFace] Request error: {e}")
            raise AIProviderError(f"خطأ في الاتصال بـ HuggingFace: {str(e)[:100]}")
    
    def image_to_text(self, image_path: str) -> str:
        """Generate caption/description for an image."""
        return self.analyze_image(image_path)
    
    def visual_qa(self, image_path: str, question: str) -> str:
        """Answer a question about an image."""
        return self.analyze_image(image_path, question=question)


class CacheManager:
    """
    Smart caching system for AI requests.
    Uses file content hashing for cache keys.
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_parts = list(args)
        key_parts.extend(sorted(kwargs.items()))
        key_string = str(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    def _file_hash(self, file_path: str) -> str:
        """Generate hash from file content."""
        if not os.path.exists(file_path):
            return ""
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self._lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl_seconds:
                    self.hits += 1
                    logger.debug(f"[Cache] Hit for key: {key[:8]}...")
                    return value
                else:
                    del self.cache[key]
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Store value in cache."""
        with self._lock:
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache, key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
            
            self.cache[key] = (value, time.time())
            logger.debug(f"[Cache] Stored key: {key[:8]}...")
    
    def get_or_compute(
        self,
        compute_fn,
        cache_key: str = None,
        file_path: str = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Get from cache or compute and store result.
        
        Args:
            compute_fn: Function to compute result if not cached
            cache_key: Optional explicit cache key
            file_path: Optional file path to include in cache key
            *args, **kwargs: Arguments for compute_fn
        """
        if file_path:
            file_hash = self._file_hash(file_path)
            key = self._generate_key(file_hash, *args, **kwargs)
        elif cache_key:
            key = cache_key
        else:
            key = self._generate_key(*args, **kwargs)
        
        cached = self.get(key)
        if cached is not None:
            return cached
        
        result = compute_fn(*args, **kwargs)
        self.set(key, result)
        return result
    
    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self.cache.clear()
            logger.info("[Cache] Cleared all entries")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.1f}%"
            }


class RateLimiter:
    """
    Rate limiting for AI requests per session/user.
    """
    
    def __init__(
        self,
        max_requests: int = 30,
        window_seconds: int = 1200,
        max_audio_per_session: int = 10,
        max_long_audio_per_session: int = 3
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_audio_per_session = max_audio_per_session
        self.max_long_audio_per_session = max_long_audio_per_session
        self.request_log: Dict[str, list] = defaultdict(list)
        self.audio_count: Dict[str, int] = defaultdict(int)
        self.long_audio_count: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def _clean_old_requests(self, session_id: str) -> None:
        """Remove requests outside the time window."""
        cutoff = time.time() - self.window_seconds
        self.request_log[session_id] = [
            t for t in self.request_log[session_id] if t > cutoff
        ]
    
    def check_limit(self, session_id: str) -> Tuple[bool, int, int]:
        """
        Check if request is allowed.
        
        Returns:
            Tuple of (allowed, remaining, reset_minutes)
        """
        with self._lock:
            self._clean_old_requests(session_id)
            current_count = len(self.request_log[session_id])
            remaining = max(0, self.max_requests - current_count)
            
            if current_count >= self.max_requests:
                oldest = min(self.request_log[session_id]) if self.request_log[session_id] else time.time()
                reset_time = int((oldest + self.window_seconds - time.time()) / 60)
                return False, 0, max(1, reset_time)
            
            return True, remaining, 0
    
    def record_request(self, session_id: str, request_type: str = "general") -> None:
        """Record a request for rate limiting."""
        with self._lock:
            self.request_log[session_id].append(time.time())
            
            if request_type == "audio":
                self.audio_count[session_id] += 1
            elif request_type == "long_audio":
                self.long_audio_count[session_id] += 1
    
    def check_audio_limit(self, session_id: str, is_long: bool = False) -> Tuple[bool, str]:
        """
        Check audio-specific limits.
        
        Returns:
            Tuple of (allowed, error_message)
        """
        with self._lock:
            if is_long:
                if self.long_audio_count[session_id] >= self.max_long_audio_per_session:
                    return False, (
                        f"تم بلوغ الحد الأقصى للفيديوهات الطويلة ({self.max_long_audio_per_session}) لهذه الجلسة. "
                        "يرجى المحاولة لاحقاً."
                    )
            else:
                if self.audio_count[session_id] >= self.max_audio_per_session:
                    return False, (
                        f"تم بلوغ الحد الأقصى للتحويلات الصوتية ({self.max_audio_per_session}) لهذه الجلسة. "
                        "يرجى المحاولة لاحقاً."
                    )
            return True, ""
    
    def get_stats(self, session_id: str) -> Dict[str, Any]:
        """Get rate limit stats for a session."""
        with self._lock:
            self._clean_old_requests(session_id)
            return {
                "requests_used": len(self.request_log[session_id]),
                "requests_limit": self.max_requests,
                "audio_count": self.audio_count.get(session_id, 0),
                "long_audio_count": self.long_audio_count.get(session_id, 0)
            }


class AIManager:
    """
    Unified AI Manager with provider routing, caching, and rate limiting.
    
    This is the main interface for all AI operations in the application.
    """
    
    def __init__(self):
        self.groq = GroqProvider()
        self.huggingface = HuggingFaceProvider()
        self.cache = CacheManager(max_size=500, ttl_seconds=3600)
        self.rate_limiter = RateLimiter()
        
        self.request_log: list = []
        self.daily_stats = defaultdict(lambda: {
            "total": 0,
            "success": 0,
            "failed": 0,
            "by_type": defaultdict(int),
            "by_provider": defaultdict(int)
        })
        self._lock = threading.Lock()
        self._db_initialized = False
        
        logger.info(f"[AIManager] Initialized")
        logger.info(f"[AIManager] Groq configured: {self.groq.is_configured}")
        logger.info(f"[AIManager] HuggingFace configured: {self.huggingface.is_configured}")
    
    def _get_session_id(self) -> str:
        """Get session ID from Flask request or generate one."""
        try:
            from flask import request
            return request.cookies.get('arkan_session', 'default_session')
        except:
            return 'default_session'
    
    def _log_request(
        self,
        provider: str,
        operation: str,
        success: bool,
        error_type: str = None,
        duration_seconds: float = 0
    ) -> None:
        """Log AI request for analytics."""
        with self._lock:
            today = datetime.utcnow().date().isoformat()
            stats = self.daily_stats[today]
            stats["total"] += 1
            stats["by_type"][operation] += 1
            stats["by_provider"][provider] += 1
            
            if success:
                stats["success"] += 1
            else:
                stats["failed"] += 1
            
            self.request_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "provider": provider,
                "operation": operation,
                "success": success,
                "error_type": error_type,
                "duration": duration_seconds
            })
            
            if len(self.request_log) > 100:
                self.request_log = self.request_log[-100:]
    
    def call_llm(
        self,
        prompt: str,
        system_prompt: str = None,
        operation: str = "llm",
        session_id: str = None,
        use_cache: bool = True
    ) -> str:
        """
        Call LLM for text generation (uses Groq).
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            operation: Operation name for logging
            session_id: Session ID for rate limiting
            use_cache: Whether to use caching
            
        Returns:
            Generated text
        """
        session_id = session_id or self._get_session_id()
        
        allowed, remaining, reset_time = self.rate_limiter.check_limit(session_id)
        if not allowed:
            raise RateLimitError(
                f"تم بلوغ الحد المسموح به من الطلبات. الرجاء الانتظار {reset_time} دقيقة."
            )
        
        cache_key = None
        if use_cache:
            cache_key = self.cache._generate_key("llm", prompt, system_prompt)
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"[AIManager] Cache hit for LLM request")
                return cached
        
        start_time = time.time()
        try:
            result = self.groq.chat_completion(prompt, system_prompt)
            duration = time.time() - start_time
            
            self.rate_limiter.record_request(session_id, "llm")
            self._log_request("groq", operation, True, duration_seconds=duration)
            
            if use_cache and cache_key:
                self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_request("groq", operation, False, error_type=type(e).__name__, duration_seconds=duration)
            raise
    
    def transcribe_audio(
        self,
        audio_path: str,
        language: str = None,
        operation: str = "transcription",
        session_id: str = None,
        use_cache: bool = True
    ) -> str:
        """
        Transcribe audio to text (uses Groq Whisper).
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'ar', 'en')
            operation: Operation name for logging
            session_id: Session ID for rate limiting
            use_cache: Whether to use caching
            
        Returns:
            Transcribed text
        """
        session_id = session_id or self._get_session_id()
        
        allowed, remaining, reset_time = self.rate_limiter.check_limit(session_id)
        if not allowed:
            raise RateLimitError(
                f"تم بلوغ الحد المسموح به من الطلبات. الرجاء الانتظار {reset_time} دقيقة."
            )
        
        audio_allowed, audio_error = self.rate_limiter.check_audio_limit(session_id)
        if not audio_allowed:
            raise RateLimitError(audio_error)
        
        if use_cache:
            cache_key = self.cache._generate_key(
                "transcription",
                self.cache._file_hash(audio_path),
                language
            )
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"[AIManager] Cache hit for transcription")
                return cached
        
        start_time = time.time()
        try:
            result = self.groq.transcribe_audio(audio_path, language)
            duration = time.time() - start_time
            
            self.rate_limiter.record_request(session_id, "audio")
            self._log_request("groq", operation, True, duration_seconds=duration)
            
            if use_cache:
                self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_request("groq", operation, False, error_type=type(e).__name__, duration_seconds=duration)
            raise
    
    def analyze_image(
        self,
        image_path: str,
        question: str = None,
        operation: str = "vision",
        session_id: str = None,
        use_cache: bool = True
    ) -> str:
        """
        Analyze image (uses HuggingFace).
        
        Args:
            image_path: Path to image file
            question: Optional question about the image
            operation: Operation name for logging
            session_id: Session ID for rate limiting
            use_cache: Whether to use caching
            
        Returns:
            Analysis result
        """
        session_id = session_id or self._get_session_id()
        
        allowed, remaining, reset_time = self.rate_limiter.check_limit(session_id)
        if not allowed:
            raise RateLimitError(
                f"تم بلوغ الحد المسموح به من الطلبات. الرجاء الانتظار {reset_time} دقيقة."
            )
        
        if use_cache:
            cache_key = self.cache._generate_key(
                "vision",
                self.cache._file_hash(image_path),
                question
            )
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"[AIManager] Cache hit for vision request")
                return cached
        
        start_time = time.time()
        try:
            result = self.huggingface.analyze_image(image_path, question)
            duration = time.time() - start_time
            
            self.rate_limiter.record_request(session_id, "vision")
            self._log_request("huggingface", operation, True, duration_seconds=duration)
            
            if use_cache:
                self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_request("huggingface", operation, False, error_type=type(e).__name__, duration_seconds=duration)
            raise
    
    def identify_anime(self, image_path: str, session_id: str = None) -> Optional[str]:
        """Identify anime from image using LLM with image description."""
        try:
            description = self.analyze_image(
                image_path,
                question="What anime is this from? Describe the characters and scene.",
                operation="anime_detection",
                session_id=session_id
            )
            
            if description:
                prompt = f"""Based on this image description, identify the anime:
Description: {description}

Return the response in this format: ANIME_NAME|EPISODE_INFO|DESCRIPTION
- ANIME_NAME: The official English or Romaji title
- EPISODE_INFO: Episode number if known, or 'Unknown'
- DESCRIPTION: Brief description (1-2 sentences)
- If cannot identify, return 'UNKNOWN'"""
                
                result = self.call_llm(prompt, operation="anime_identification", session_id=session_id)
                if result and result.upper() != 'UNKNOWN':
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"[AIManager] Anime identification error: {e}")
            return None
    
    def identify_podcast(self, image_path: str = None, transcript: str = None, session_id: str = None) -> Optional[str]:
        """Identify podcast from image or transcript."""
        try:
            if image_path:
                description = self.analyze_image(
                    image_path,
                    question="What podcast or show is this? Describe any visible text, logos, or hosts.",
                    operation="podcast_detection",
                    session_id=session_id
                )
                
                if description:
                    prompt = f"""Based on this image description of a podcast/show, identify it:
Description: {description}

Return the response in this format: PODCAST_NAME|HOST_NAMES|PLATFORM
- PODCAST_NAME: The podcast/show/channel name
- HOST_NAMES: Names of hosts if visible, or 'Unknown'
- PLATFORM: Where found (YouTube, Spotify, Apple Podcasts, or General)
- If cannot identify, return 'UNKNOWN'"""
                    
                    result = self.call_llm(prompt, operation="podcast_identification", session_id=session_id)
                    if result and result.upper() != 'UNKNOWN':
                        return result
            
            elif transcript:
                prompt = f"""Based on this audio transcript, identify the Podcast name, Host, or Show name.

Transcript:
{transcript[:2000]}

Instructions:
- Look for any mentions of podcast names, show names, host introductions
- Consider phrases like "welcome to...", "this is...", "you're listening to..."
- Return ONLY the podcast/show name
- If cannot identify, return 'UNKNOWN'"""
                
                result = self.call_llm(prompt, operation="podcast_from_transcript", session_id=session_id)
                if result and result.upper() != 'UNKNOWN':
                    return result.replace('"', '').replace("'", '').strip()
            
            return None
            
        except Exception as e:
            logger.error(f"[AIManager] Podcast identification error: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get AI usage statistics."""
        today = datetime.utcnow().date().isoformat()
        with self._lock:
            daily = self.daily_stats.get(today, {})
            return {
                "providers": {
                    "groq": {
                        "configured": self.groq.is_configured,
                        "healthy": self.groq.health_check() if self.groq.is_configured else False
                    },
                    "huggingface": {
                        "configured": self.huggingface.is_configured,
                        "healthy": self.huggingface.health_check() if self.huggingface.is_configured else False
                    }
                },
                "today": {
                    "total_requests": daily.get("total", 0),
                    "successful": daily.get("success", 0),
                    "failed": daily.get("failed", 0),
                    "by_type": dict(daily.get("by_type", {})),
                    "by_provider": dict(daily.get("by_provider", {}))
                },
                "cache": self.cache.stats(),
                "recent_requests": self.request_log[-20:] if self.request_log else []
            }


ai_manager = AIManager()
