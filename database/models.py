"""
Database models for SEO audit results and tracking
"""

import sqlite3
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

DATABASE_PATH = "seo_auditor.db"

@dataclass
class AuditResult:
    """Base class for audit results."""
    url: str
    audit_type: str
    timestamp: datetime
    results: Dict[str, Any]
    score: Optional[float] = None
    issues: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

@dataclass
class CrawlResult:
    """Site crawl results."""
    url: str
    total_pages: int
    crawled_pages: int
    errors: List[str]
    pages: List[Dict[str, Any]]
    timestamp: datetime

@dataclass
class PerformanceResult:
    """Performance audit results."""
    url: str
    device: str
    lcp: Optional[float]  # Largest Contentful Paint
    fid: Optional[float]  # First Input Delay
    cls: Optional[float]  # Cumulative Layout Shift
    fcp: Optional[float]  # First Contentful Paint
    lighthouse_score: Optional[int]
    timestamp: datetime

async def init_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Audit results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            audit_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            results TEXT NOT NULL,
            score REAL,
            issues TEXT,
            recommendations TEXT
        )
    ''')
    
    # Crawl results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            total_pages INTEGER,
            crawled_pages INTEGER,
            errors TEXT,
            pages TEXT,
            timestamp TEXT NOT NULL
        )
    ''')
    
    # Performance results table  
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            device TEXT NOT NULL,
            lcp REAL,
            fid REAL,
            cls REAL,
            fcp REAL,
            lighthouse_score INTEGER,
            timestamp TEXT NOT NULL
        )
    ''')
    
    # Site tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracked_sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            name TEXT,
            added_date TEXT NOT NULL,
            last_audit TEXT,
            audit_frequency TEXT DEFAULT 'weekly'
        )
    ''')
    
    conn.commit()
    conn.close()

async def save_audit_result(result: AuditResult) -> int:
    """Save audit result to database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO audit_results 
        (url, audit_type, timestamp, results, score, issues, recommendations)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        result.url,
        result.audit_type,
        result.timestamp.isoformat(),
        json.dumps(result.results),
        result.score,
        json.dumps(result.issues) if result.issues else None,
        json.dumps(result.recommendations) if result.recommendations else None
    ))
    
    audit_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return audit_id

async def save_crawl_result(result: CrawlResult) -> int:
    """Save crawl result to database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO crawl_results 
        (url, total_pages, crawled_pages, errors, pages, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        result.url,
        result.total_pages,
        result.crawled_pages,
        json.dumps(result.errors),
        json.dumps(result.pages),
        result.timestamp.isoformat()
    ))
    
    crawl_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return crawl_id

async def save_performance_result(result: PerformanceResult) -> int:
    """Save performance result to database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO performance_results 
        (url, device, lcp, fid, cls, fcp, lighthouse_score, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        result.url,
        result.device,
        result.lcp,
        result.fid,
        result.cls,
        result.fcp,
        result.lighthouse_score,
        result.timestamp.isoformat()
    ))
    
    perf_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return perf_id

async def get_audit_history(url: str, audit_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get audit history for a URL."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    query = "SELECT * FROM audit_results WHERE url = ?"
    params = [url]
    
    if audit_type:
        query += " AND audit_type = ?"
        params.append(audit_type)
    
    query += " ORDER BY timestamp DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        result = {
            'id': row[0],
            'url': row[1],
            'audit_type': row[2],
            'timestamp': row[3],
            'results': json.loads(row[4]),
            'score': row[5],
            'issues': json.loads(row[6]) if row[6] else None,
            'recommendations': json.loads(row[7]) if row[7] else None
        }
        results.append(result)
    
    conn.close()
    return results

async def get_performance_history(url: str, device: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get performance history for a URL."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    query = "SELECT * FROM performance_results WHERE url = ?"
    params = [url]
    
    if device:
        query += " AND device = ?"
        params.append(device)
    
    query += " ORDER BY timestamp DESC LIMIT 50"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        result = {
            'id': row[0],
            'url': row[1],
            'device': row[2],
            'lcp': row[3],
            'fid': row[4],
            'cls': row[5],
            'fcp': row[6],
            'lighthouse_score': row[7],
            'timestamp': row[8]
        }
        results.append(result)
    
    conn.close()
    return results