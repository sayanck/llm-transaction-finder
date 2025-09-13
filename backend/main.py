"""
FastAPI backend for LLM Transaction Pattern Finder.
Provides REST API endpoints for transaction analysis.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any, Optional
import os
import sys
from datetime import datetime

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from data_processor import TransactionProcessor
from llm_analyzer import TransactionAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LLM Transaction Pattern Finder",
    description="Analyze transaction patterns using AI to detect suspicious activities",
    version="1.0.0"
)

# Configure CORS
allowed_origins = [
    "http://localhost:3000", 
    "http://localhost:5173",
    "https://transaction-analyzer-frontend.onrender.com" 
    "https://llm-transaction-finder-1.onrender.com/" # Render frontend URL
]

# Add any additional origins from environment variable
if os.getenv("ALLOWED_ORIGINS"):
    allowed_origins.extend(os.getenv("ALLOWED_ORIGINS").split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for caching and current file
transaction_processor = None
analysis_cache = {}
last_analysis_time = None
current_data_file: Optional[str] = None

def get_transaction_processor():
    """Get or create transaction processor instance."""
    global transaction_processor, current_data_file
    if transaction_processor is None:
        data_path = current_data_file or os.path.join(os.path.dirname(__file__), "..", "Transaction_data_All.xlsx")
        transaction_processor = TransactionProcessor(data_path)
    elif current_data_file and transaction_processor.file_path != current_data_file:
        transaction_processor = TransactionProcessor(current_data_file)
    return transaction_processor

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LLM Transaction Pattern Finder API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "summary": "/api/summary",
            "patterns": "/api/patterns",
            "analyze": "/api/analyze",
            "threads": "/api/threads"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "gemini_configured": bool(os.getenv('GEMINI_API_KEY')),
        "current_file": current_data_file
    }

@app.get("/api/current-file")
async def get_current_file():
    """Return info about the currently loaded data file."""
    return {
        "success": True,
        "data": {
            "file_path": current_data_file,
            "using_default": current_data_file is None
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV or Excel file and set it as the active dataset."""
    global current_data_file, transaction_processor, analysis_cache, last_analysis_time
    try:
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        filename = file.filename or f"uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        # Basic security: strip path
        filename = os.path.basename(filename)
        save_path = os.path.join(uploads_dir, filename)

        with open(save_path, 'wb') as out_file:
            content = await file.read()
            out_file.write(content)

        # Validate extension
        allowed_ext = ('.csv', '.xlsx', '.xls')
        if not filename.lower().endswith(allowed_ext):
            os.remove(save_path)
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload CSV or Excel.")

        # Prepare to swap files: keep reference to old file (if any)
        old_file = current_data_file

        # Tentatively set as current and reset caches
        current_data_file = save_path
        transaction_processor = None
        analysis_cache = {}
        last_analysis_time = None

        # Try loading to validate file structure quickly
        processor = get_transaction_processor()
        processor.load_data()

        # If validation passed, delete old uploaded file if it exists inside uploads dir
        if old_file and os.path.commonpath([os.path.abspath(old_file), os.path.abspath(uploads_dir)]) == os.path.abspath(uploads_dir):
            try:
                if os.path.abspath(old_file) != os.path.abspath(save_path) and os.path.exists(old_file):
                    os.remove(old_file)
                    logger.info(f"Removed old uploaded file: {old_file}")
            except Exception as del_err:
                logger.warning(f"Could not delete old file {old_file}: {del_err}")

        return JSONResponse(content={
            "success": True,
            "message": "File uploaded and set as active dataset",
            "data": {"file_path": current_data_file}
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        # Rollback current_data_file if new upload fails
        try:
            if 'save_path' in locals() and os.path.exists(save_path):
                os.remove(save_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/summary")
async def get_summary():
    """Get transaction data summary statistics."""
    try:
        processor = get_transaction_processor()
        processor.load_data()
        summary = processor.get_summary_stats()
        
        return JSONResponse(content={
            "success": True,
            "data": summary,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/patterns")
async def get_patterns():
    """Get identified transaction patterns."""
    try:
        processor = get_transaction_processor()
        patterns = processor.identify_potential_patterns()
        
        return JSONResponse(content={
            "success": True,
            "data": patterns,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_patterns(background_tasks: BackgroundTasks):
    """Trigger LLM analysis of transaction patterns with optimized performance."""
    global analysis_cache, last_analysis_time
    
    try:
        # Check if we have a recent analysis cached (extended cache time)
        if (last_analysis_time and 
            (datetime.now() - last_analysis_time).total_seconds() < 1800 and  # 30 minutes cache
            analysis_cache):
            return JSONResponse(content={
                "success": True,
                "data": analysis_cache,
                "cached": True,
                "timestamp": last_analysis_time.isoformat()
            })
        
        # Get patterns and summary
        processor = get_transaction_processor()
        patterns = processor.identify_potential_patterns()
        summary = processor.get_summary_stats()
        
        # Check if Gemini API key is configured
        if not os.getenv('GEMINI_API_KEY'):
            # Return mock analysis if no API key
            mock_analysis = create_mock_analysis(patterns, summary)
            analysis_cache = mock_analysis
            last_analysis_time = datetime.now()
            
            return JSONResponse(content={
                "success": True,
                "data": mock_analysis,
                "mock": True,
                "message": "Using mock analysis - configure GEMINI_API_KEY for real AI analysis",
                "timestamp": last_analysis_time.isoformat()
            })
        
        # Perform optimized LLM analysis
        analyzer = TransactionAnalyzer()
        analysis = analyzer.analyze_patterns(patterns, summary)
        
        # Cache results
        analysis_cache = analysis
        last_analysis_time = datetime.now()
        
        return JSONResponse(content={
            "success": True,
            "data": analysis,
            "timestamp": last_analysis_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        # Return partial results if available
        if analysis_cache:
            return JSONResponse(content={
                "success": True,
                "data": analysis_cache,
                "partial": True,
                "message": "Using cached analysis due to processing error",
                "timestamp": last_analysis_time.isoformat() if last_analysis_time else datetime.now().isoformat()
            })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-progressive")
async def analyze_patterns_progressive():
    """Progressive analysis endpoint that returns results as they become available."""
    global analysis_cache, last_analysis_time
    
    try:
        # Check cache first
        if (last_analysis_time and 
            (datetime.now() - last_analysis_time).total_seconds() < 1800 and
            analysis_cache):
            return JSONResponse(content={
                "success": True,
                "data": analysis_cache,
                "cached": True,
                "timestamp": last_analysis_time.isoformat()
            })
        
        # Get patterns and summary
        processor = get_transaction_processor()
        patterns = processor.identify_potential_patterns()
        summary = processor.get_summary_stats()
        
        # Check if Gemini API key is configured
        if not os.getenv('GEMINI_API_KEY'):
            mock_analysis = create_mock_analysis(patterns, summary)
            analysis_cache = mock_analysis
            last_analysis_time = datetime.now()
            
            return JSONResponse(content={
                "success": True,
                "data": mock_analysis,
                "mock": True,
                "message": "Using mock analysis - configure GEMINI_API_KEY for real AI analysis",
                "timestamp": last_analysis_time.isoformat()
            })
        
        # Perform progressive analysis
        analyzer = TransactionAnalyzer()
        analysis = analyzer.analyze_patterns(patterns, summary)
        
        # Cache results
        analysis_cache = analysis
        last_analysis_time = datetime.now()
        
        return JSONResponse(content={
            "success": True,
            "data": analysis,
            "timestamp": last_analysis_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in progressive analysis: {e}")
        if analysis_cache:
            return JSONResponse(content={
                "success": True,
                "data": analysis_cache,
                "partial": True,
                "message": "Using cached analysis due to processing error",
                "timestamp": last_analysis_time.isoformat() if last_analysis_time else datetime.now().isoformat()
            })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/threads")
async def get_threads():
    """Get all identified suspicious threads."""
    global analysis_cache
    
    if not analysis_cache:
        raise HTTPException(status_code=404, detail="No analysis available. Run /api/analyze first.")
    
    # Collect all threads from analysis
    all_threads = []
    
    for pattern_type, analysis in analysis_cache.items():
        if isinstance(analysis, dict) and 'threads' in analysis:
            for thread in analysis['threads']:
                thread['pattern_type'] = pattern_type
                all_threads.append(thread)
    
    # Sort by risk level
    risk_order = {'high': 3, 'medium': 2, 'low': 1}
    all_threads.sort(key=lambda x: risk_order.get(x.get('risk_level', 'low'), 1), reverse=True)
    
    return JSONResponse(content={
        "success": True,
        "data": {
            "threads": all_threads,
            "total_count": len(all_threads),
            "risk_distribution": {
                "high": len([t for t in all_threads if t.get('risk_level') == 'high']),
                "medium": len([t for t in all_threads if t.get('risk_level') == 'medium']),
                "low": len([t for t in all_threads if t.get('risk_level') == 'low'])
            }
        },
        "timestamp": datetime.now().isoformat()
    })

def create_mock_analysis(patterns: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
    """Create mock analysis when Gemini API is not available."""
    mock_analysis = {}
    
    for pattern_type, pattern_data in patterns.items():
        if not pattern_data:
            continue
            
        # Create mock threads based on pattern data
        threads = []
        
        if pattern_type == 'frequent_pairs' and len(pattern_data) > 0:
            for i, pair in enumerate(pattern_data[:3]):  # Top 3 pairs
                if pair['transaction_count'] >= 5:  # High frequency threshold
                    threads.append({
                        'thread_id': f'freq_pair_{i}',
                        'description': f"High frequency transactions between {pair['sender_name']} and {pair['receiver_name']} ({pair['transaction_count']} transactions)",
                        'participants': [pair['sender_name'], pair['receiver_name']],
                        'risk_level': 'high' if pair['transaction_count'] >= 8 else 'medium',
                        'evidence': [
                            f"Total of {pair['transaction_count']} transactions",
                            f"Average amount: ${pair['average_amount']:,.2f}",
                            f"Total amount: ${pair['total_amount']:,.2f}"
                        ],
                        'transactions_involved': [str(t['transaction_id']) for t in pair['sample_transactions']],
                        'potential_violation': 'Potential layering or structuring'
                    })
        
        elif pattern_type == 'round_amounts' and len(pattern_data) > 5:
            threads.append({
                'thread_id': 'round_amounts_1',
                'description': f"Multiple round number transactions detected ({len(pattern_data)} transactions)",
                'participants': list(set([t['user_name'] for t in pattern_data[:5]])),
                'risk_level': 'medium',
                'evidence': [
                    f"{len(pattern_data)} transactions with round amounts",
                    "Potential structuring to avoid reporting thresholds"
                ],
                'transactions_involved': [str(t['transaction_id']) for t in pattern_data[:5]],
                'potential_violation': 'Potential structuring'
            })
        
        elif pattern_type == 'high_activity_periods' and len(pattern_data) > 0:
            for period in pattern_data[:2]:  # Top 2 periods
                if period['transaction_count'] > 10:
                    threads.append({
                        'thread_id': f'high_activity_{period["time_period"][:10]}',
                        'description': f"Unusual activity spike: {period['transaction_count']} transactions in one hour",
                        'participants': [],
                        'risk_level': 'medium',
                        'evidence': [
                            f"{period['transaction_count']} transactions in one hour",
                            f"Total amount: ${period['total_amount']:,.2f}",
                            f"Unique users: {period['unique_users']}"
                        ],
                        'transactions_involved': [str(t['transaction_id']) for t in period['sample_transactions']],
                        'potential_violation': 'Coordinated suspicious activity'
                    })
        
        mock_analysis[pattern_type] = {
            'threads': threads,
            'risk_level': 'high' if any(t['risk_level'] == 'high' for t in threads) else 'medium' if threads else 'low',
            'summary': f"Mock analysis for {pattern_type}: {len(threads)} suspicious threads identified"
        }
    
    # Add overall assessment
    all_threads = []
    for analysis in mock_analysis.values():
        all_threads.extend(analysis['threads'])
    
    mock_analysis['overall_assessment'] = {
        'total_threads': len(all_threads),
        'overall_risk_level': 'high' if len([t for t in all_threads if t['risk_level'] == 'high']) >= 2 else 'medium',
        'executive_summary': f"Mock analysis identified {len(all_threads)} suspicious transaction threads across multiple pattern types. Key concerns include high-frequency user pairs and potential structuring activities.",
        'pattern_summary': {
            pattern_type: {
                'thread_count': len(analysis['threads']),
                'risk_level': analysis['risk_level']
            }
            for pattern_type, analysis in mock_analysis.items()
            if pattern_type != 'overall_assessment'
        },
        'top_threats': sorted(all_threads, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}.get(x.get('risk_level', 'low'), 1), reverse=True)[:5]
    }
    
    return mock_analysis

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
