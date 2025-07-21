#!/usr/bin/env python3
"""
SpaCy Enhancer Service
Provides semantic analysis and contextual suggestions for text correction
"""

import os
import logging
import time
from typing import List, Dict, Optional, Any
from datetime import datetime

import spacy
import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
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
REQUEST_COUNT = Counter('spacy_requests_total', 'Total requests to SpaCy service', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('spacy_request_duration_seconds', 'Request duration in seconds')
PROCESSING_DURATION = Histogram('spacy_processing_duration_seconds', 'Text processing duration in seconds')
ERROR_COUNT = Counter('spacy_errors_total', 'Total errors in SpaCy service', ['error_type'])

# Pydantic models
class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
    include_entities: bool = Field(default=True, description="Include named entity recognition")
    include_pos: bool = Field(default=True, description="Include part-of-speech tagging")
    include_dependencies: bool = Field(default=False, description="Include dependency parsing")
    include_suggestions: bool = Field(default=True, description="Include contextual suggestions")

class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int
    confidence: float

class Token(BaseModel):
    text: str
    pos: str
    tag: str
    lemma: str
    is_alpha: bool
    is_stop: bool

class Suggestion(BaseModel):
    original: str
    suggestion: str
    confidence: float
    reason: str
    start: int
    end: int

class AnalysisResponse(BaseModel):
    text: str
    language: str
    entities: List[Entity] = []
    tokens: List[Token] = []
    suggestions: List[Suggestion] = []
    processing_time: float
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    spacy_model: str
    uptime: float
    timestamp: datetime

# SpaCy service class
class SpaCyService:
    def __init__(self):
        self.nlp = None
        self.model_name = os.getenv('SPACY_MODEL', 'pt_core_news_lg')
        self.start_time = time.time()
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def load_model(self):
        """Load SpaCy model with retry logic"""
        try:
            logger.info("Loading SpaCy model", model=self.model_name)
            self.nlp = spacy.load(self.model_name)
            logger.info("SpaCy model loaded successfully", model=self.model_name)
        except OSError as e:
            logger.error("Failed to load SpaCy model", error=str(e), model=self.model_name)
            # Fallback to smaller model
            try:
                self.model_name = 'pt_core_news_sm'
                logger.warning("Trying fallback model", model=self.model_name)
                self.nlp = spacy.load(self.model_name)
                logger.info("Fallback model loaded successfully", model=self.model_name)
            except OSError:
                raise RuntimeError("Unable to load any Portuguese SpaCy model")
    
    def analyze_text(self, request: TextRequest) -> AnalysisResponse:
        """Analyze text using SpaCy NLP pipeline"""
        start_time = time.time()
        
        try:
            # Process text with SpaCy
            doc = self.nlp(request.text)
            
            # Extract entities
            entities = []
            if request.include_entities:
                for ent in doc.ents:
                    entities.append(Entity(
                        text=ent.text,
                        label=ent.label_,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=ent._.get('confidence', 0.0) if hasattr(ent._, 'confidence') else 0.0
                    ))
            
            # Extract tokens
            tokens = []
            if request.include_pos:
                for token in doc:
                    tokens.append(Token(
                        text=token.text,
                        pos=token.pos_,
                        tag=token.tag_,
                        lemma=token.lemma_,
                        is_alpha=token.is_alpha,
                        is_stop=token.is_stop
                    ))
            
            # Generate contextual suggestions
            suggestions = []
            if request.include_suggestions:
                suggestions = self._generate_suggestions(doc)
            
            processing_time = time.time() - start_time
            PROCESSING_DURATION.observe(processing_time)
            
            return AnalysisResponse(
                text=request.text,
                language=doc.lang_,
                entities=entities,
                tokens=tokens,
                suggestions=suggestions,
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            logger.error("Error analyzing text", error=str(e), text_length=len(request.text))
            raise HTTPException(status_code=500, detail=f"Error analyzing text: {str(e)}")
    
    def _generate_suggestions(self, doc) -> List[Suggestion]:
        """Generate contextual suggestions for text improvement"""
        suggestions = []
        
        # Common grammar patterns to suggest improvements
        for token in doc:
            # Suggest formal alternatives for informal words
            informal_formal = {
                'tá': 'está',
                'né': 'não é',
                'pra': 'para',
                'pro': 'para o',
                'numa': 'em uma',
                'numa': 'em uma',
                'dele': 'de ele',
                'dela': 'de ela'
            }
            
            if token.text.lower() in informal_formal:
                suggestions.append(Suggestion(
                    original=token.text,
                    suggestion=informal_formal[token.text.lower()],
                    confidence=0.8,
                    reason="Sugestão de linguagem formal",
                    start=token.idx,
                    end=token.idx + len(token.text)
                ))
            
            # Detect potential verb conjugation issues
            if token.pos_ == 'VERB' and token.tag_.startswith('V'):
                # This is a simplified example - in production, you'd use more sophisticated rules
                if token.text.endswith('ão') and token.head.text in ['eu', 'tu', 'ele', 'ela']:
                    potential_error = True
                    if potential_error:
                        suggestions.append(Suggestion(
                            original=token.text,
                            suggestion=token.lemma_,
                            confidence=0.6,
                            reason="Possível erro de conjugação verbal",
                            start=token.idx,
                            end=token.idx + len(token.text)
                        ))
        
        return suggestions

# Initialize FastAPI app
app = FastAPI(
    title="SpaCy Enhancer Service",
    description="Semantic analysis and contextual suggestions for Portuguese text",
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

# Initialize SpaCy service
spacy_service = SpaCyService()

@app.on_event("startup")
async def startup_event():
    """Initialize the SpaCy model on startup"""
    try:
        spacy_service.load_model()
        logger.info("SpaCy Enhancer Service started successfully")
    except Exception as e:
        logger.error("Failed to start SpaCy service", error=str(e))
        raise

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and measure duration"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    
    logger.info(
        "Request processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
    
    return response

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="SpaCy Enhancer",
        version="2.0.0",
        spacy_model=spacy_service.model_name,
        uptime=time.time() - spacy_service.start_time,
        timestamp=datetime.now()
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: TextRequest):
    """Analyze text and provide semantic enhancements"""
    try:
        if not spacy_service.nlp:
            raise HTTPException(status_code=503, detail="SpaCy model not loaded")
        
        result = spacy_service.analyze_text(request)
        
        logger.info(
            "Text analyzed successfully",
            text_length=len(request.text),
            entities_found=len(result.entities),
            suggestions_made=len(result.suggestions),
            processing_time=result.processing_time
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        ERROR_COUNT.labels(error_type=type(e).__name__).inc()
        logger.error("Unexpected error in analyze endpoint", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "SpaCy Enhancer",
        "version": "2.0.0",
        "description": "Semantic analysis and contextual suggestions for Portuguese text",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv('SPACY_PORT', 8020))
    workers = int(os.getenv('WORKERS', 2))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        access_log=True
    )
