#!/usr/bin/env python3
"""
API Gateway Service
Orchestrates requests between LanguageTool and SpaCy services
"""

import os
import asyncio
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

import httpx
import structlog
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import redis
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('gateway_requests_total', 'Total requests to gateway', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('gateway_request_duration_seconds', 'Request duration in seconds')
LANGUAGETOOL_REQUESTS = Counter('languagetool_requests_total', 'Requests to LanguageTool', ['status'])
SPACY_REQUESTS = Counter('spacy_requests_total', 'Requests to SpaCy', ['status'])
CORRECTION_DURATION = Histogram('correction_duration_seconds', 'Time to complete correction')

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize Redis for caching (optional)
redis_client = None

# Pydantic models
class CorrectionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="Text to correct")
    language: str = Field(default="pt-BR", description="Language code")
    enable_spacy: bool = Field(default=True, description="Enable SpaCy semantic analysis")
    include_suggestions: bool = Field(default=True, description="Include improvement suggestions")
    threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Correction confidence threshold")

class LanguageToolError(BaseModel):
    offset: int
    length: int
    rule_id: str
    message: str
    shortMessage: str
    suggestions: List[str]
    category: str
    confidence: float

class SpaCySuggestion(BaseModel):
    original: str
    suggestion: str
    confidence: float
    reason: str
    start: int
    end: int

class CorrectionResponse(BaseModel):
    original_text: str
    corrected_text: str
    languagetool_errors: List[LanguageToolError]
    spacy_suggestions: List[SpaCySuggestion]
    processing_time: float
    timestamp: datetime
    language: str
    confidence_score: float

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    dependencies: Dict[str, str]
    uptime: float
    timestamp: datetime

# Service orchestrator
class CorrectionOrchestrator:
    def __init__(self):
        self.languagetool_url = os.getenv('LANGUAGETOOL_URL', 'http://languagetool:8010')
        self.spacy_url = os.getenv('SPACY_URL', 'http://spacy-enhancer:8020')
        self.start_time = time.time()
        
    async def _call_languagetool(self, text: str, language: str = "pt-BR") -> Dict[str, Any]:
        """Call LanguageTool service for grammar checking"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.languagetool_url}/v2/check",
                    data={
                        "text": text,
                        "language": language,
                        "enabledOnly": "false"
                    }
                )
                
                if response.status_code == 200:
                    LANGUAGETOOL_REQUESTS.labels(status="success").inc()
                    return response.json()
                else:
                    LANGUAGETOOL_REQUESTS.labels(status="error").inc()
                    logger.error("LanguageTool error", status_code=response.status_code, response=response.text)
                    return {"matches": []}
                    
        except Exception as e:
            LANGUAGETOOL_REQUESTS.labels(status="error").inc()
            logger.error("LanguageTool request failed", error=str(e))
            return {"matches": []}
    
    async def _call_spacy(self, text: str) -> Dict[str, Any]:
        """Call SpaCy service for semantic analysis"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.spacy_url}/analyze",
                    json={
                        "text": text,
                        "include_entities": False,
                        "include_pos": False,
                        "include_dependencies": False,
                        "include_suggestions": True
                    }
                )
                
                if response.status_code == 200:
                    SPACY_REQUESTS.labels(status="success").inc()
                    return response.json()
                else:
                    SPACY_REQUESTS.labels(status="error").inc()
                    logger.error("SpaCy error", status_code=response.status_code, response=response.text)
                    return {"suggestions": []}
                    
        except Exception as e:
            SPACY_REQUESTS.labels(status="error").inc()
            logger.error("SpaCy request failed", error=str(e))
            return {"suggestions": []}
    
    def _apply_corrections(self, text: str, errors: List[Dict], threshold: float = 0.3) -> str:
        """Apply corrections to text based on LanguageTool suggestions"""
        corrected_text = text
        offset_adjustment = 0
        
        # Sort errors by offset to apply corrections from left to right
        sorted_errors = sorted(errors, key=lambda x: x.get('offset', 0))
        
        for error in sorted_errors:
            if not error.get('replacements'):
                continue
                
            # Get the best suggestion
            best_replacement = error['replacements'][0]['value']
            
            # Calculate confidence (simplified)
            confidence = 1.0 - (error.get('offset', 0) / len(text))
            
            if confidence >= threshold:
                start = error['offset'] + offset_adjustment
                end = start + error['length']
                
                # Apply correction
                corrected_text = corrected_text[:start] + best_replacement + corrected_text[end:]
                
                # Adjust offset for subsequent corrections
                offset_adjustment += len(best_replacement) - error['length']
        
        return corrected_text
    
    async def correct_text(self, request: CorrectionRequest) -> CorrectionResponse:
        """Orchestrate text correction using both services"""
        start_time = time.time()
        
        try:
            # Call LanguageTool and SpaCy concurrently
            tasks = [self._call_languagetool(request.text, request.language)]
            
            if request.enable_spacy:
                tasks.append(self._call_spacy(request.text))
            
            results = await asyncio.gather(*tasks)
            
            languagetool_result = results[0]
            spacy_result = results[1] if len(results) > 1 else {"suggestions": []}
            
            # Process LanguageTool errors
            lt_errors = []
            for match in languagetool_result.get('matches', []):
                lt_errors.append(LanguageToolError(
                    offset=match.get('offset', 0),
                    length=match.get('length', 0),
                    rule_id=match.get('rule', {}).get('id', ''),
                    message=match.get('message', ''),
                    shortMessage=match.get('shortMessage', ''),
                    suggestions=[rep['value'] for rep in match.get('replacements', [])[:3]],
                    category=match.get('rule', {}).get('category', {}).get('name', ''),
                    confidence=1.0  # LanguageTool doesn't provide confidence, so we use 1.0
                ))
            
            # Process SpaCy suggestions
            spacy_suggestions = []
            for suggestion in spacy_result.get('suggestions', []):
                spacy_suggestions.append(SpaCySuggestion(
                    original=suggestion.get('original', ''),
                    suggestion=suggestion.get('suggestion', ''),
                    confidence=suggestion.get('confidence', 0.0),
                    reason=suggestion.get('reason', ''),
                    start=suggestion.get('start', 0),
                    end=suggestion.get('end', 0)
                ))
            
            # Apply corrections
            corrected_text = self._apply_corrections(
                request.text, 
                languagetool_result.get('matches', []), 
                request.threshold
            )
            
            # Calculate overall confidence score
            total_errors = len(lt_errors)
            confidence_score = max(0.0, 1.0 - (total_errors / max(len(request.text.split()), 1)))
            
            processing_time = time.time() - start_time
            CORRECTION_DURATION.observe(processing_time)
            
            return CorrectionResponse(
                original_text=request.text,
                corrected_text=corrected_text,
                languagetool_errors=lt_errors,
                spacy_suggestions=spacy_suggestions,
                processing_time=processing_time,
                timestamp=datetime.now(),
                language=request.language,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error("Error in correction orchestration", error=str(e))
            raise HTTPException(status_code=500, detail=f"Correction failed: {str(e)}")
    
    async def check_dependencies(self) -> Dict[str, str]:
        """Check health of dependent services"""
        dependencies = {}
        
        # Check LanguageTool
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.languagetool_url}/v2/check?text=test")
                dependencies["languagetool"] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            dependencies["languagetool"] = "unreachable"
        
        # Check SpaCy
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.spacy_url}/health")
                dependencies["spacy"] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            dependencies["spacy"] = "unreachable"
        
        return dependencies

# Initialize FastAPI app
app = FastAPI(
    title="LanguageTool Corrector API Gateway",
    description="Orchestration service for text correction using LanguageTool and SpaCy",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Initialize orchestrator
orchestrator = CorrectionOrchestrator()

# Optional Redis initialization
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global redis_client
    
    try:
        # Try to connect to Redis for caching
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        redis_client.ping()
        logger.info("Redis connection established")
    except:
        logger.warning("Redis not available, caching disabled")
        redis_client = None
    
    logger.info("API Gateway started successfully")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and measure duration"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=request.url.path, 
        status=response.status_code
    ).inc()
    
    logger.info(
        "Request processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration,
        client_ip=get_remote_address(request)
    )
    
    return response

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with dependency status"""
    dependencies = await orchestrator.check_dependencies()
    
    # Determine overall health
    overall_status = "healthy"
    if dependencies.get("languagetool") != "healthy":
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        service="API Gateway",
        version="2.0.0",
        dependencies=dependencies,
        uptime=time.time() - orchestrator.start_time,
        timestamp=datetime.now()
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.post("/correct", response_model=CorrectionResponse)
# @limiter.limit("100/minute")  # Rate limit - temporarily disabled
async def correct_text(correction_request: CorrectionRequest, request: Request = None):
    """Main text correction endpoint"""
    try:
        # Check cache first (if Redis is available)
        cache_key = None
        if redis_client:
            cache_key = f"correction:{hash(correction_request.text)}:{correction_request.language}:{correction_request.threshold}"
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.info("Cache hit for correction request")
                return CorrectionResponse.parse_raw(cached_result)
        
        # Perform correction
        result = await orchestrator.correct_text(correction_request)
        
        # Cache result (if Redis is available)
        if redis_client and cache_key:
            redis_client.setex(cache_key, 3600, result.json())  # Cache for 1 hour
        
        logger.info(
            "Text corrected successfully",
            original_length=len(correction_request.text),
            corrected_length=len(result.corrected_text),
            errors_found=len(result.languagetool_errors),
            suggestions_made=len(result.spacy_suggestions),
            processing_time=result.processing_time
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in correct endpoint", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Backward compatibility endpoint
@app.post("/corrigir", response_model=CorrectionResponse)
# @limiter.limit("100/minute")  # Rate limit - temporarily disabled
async def corrigir_texto(request_data: dict, request: Request = None):
    """Legacy endpoint for backward compatibility"""
    try:
        # Convert legacy request format
        correction_request = CorrectionRequest(
            text=request_data.get("text", ""),
            language=request_data.get("language", "pt-BR"),
            threshold=request_data.get("threshold", 0.3)
        )
        
        return await correct_text(correction_request, request)
        
    except Exception as e:
        logger.error("Error in legacy endpoint", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid request format")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "LanguageTool Corrector API Gateway",
        "version": "2.0.0",
        "description": "Advanced text correction using LanguageTool and SpaCy",
        "endpoints": {
            "correct": "/correct",
            "corrigir": "/corrigir (legacy)",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs"
        },
        "features": [
            "Grammar and spelling correction",
            "Semantic analysis",
            "Contextual suggestions",
            "Rate limiting",
            "Caching",
            "Monitoring"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv('GATEWAY_PORT', 8000))
    workers = int(os.getenv('GATEWAY_WORKERS', 4))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        access_log=True
    )
