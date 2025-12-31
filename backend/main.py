import sqlite3
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI()

# Path Configuration - use absolute paths for deployment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data")
DB_PATH = os.path.join(DATA_DIR, "artworks.db")
IMAGES_DIR = os.path.join(DATA_DIR, "images")

# CORS configuration - set ALLOWED_ORIGINS env var in production
# Example: ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Artwork(BaseModel):
    id: str
    title: Optional[str] = None
    artist: Optional[str] = None
    date: Optional[str] = None
    medium: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    credit: Optional[str] = None
    dimensions: Optional[str] = None
    department: Optional[str] = None
    url: Optional[str] = None

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def map_row_to_artwork(row, base_url: str = "http://127.0.0.1:32001") -> Artwork:
    # Check for local image
    final_image_url = row['image_path'] if row['image_path'] else row['thumbnail_path']
    
    # Check for local image with various extensions
    extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG', '.webp', '.gif']
    for ext in extensions:
        image_filename = f"{row['artwork_id']}{ext}"
        local_image_path = os.path.join(IMAGES_DIR, image_filename)
        if os.path.exists(local_image_path):
            final_image_url = f"{base_url}/images/{image_filename}"
            break
    
    # Data Cleaning
    title = row['title']
    if title:
        if title.startswith(') '):
            title = title[2:]
        elif title.startswith(')'):
             title = title[1:]
        title = title.strip()

    artist = row['artist']
    if artist and '(' in artist and ')' not in artist:
        artist = artist + ')'

    # Clean category for department (replace _ with space, title case)
    department = row['category']
    if department:
        department = department.replace('_', ' ').title()

    return Artwork(
        id=row['artwork_id'],
        title=title,
        artist=artist,
        date=row['date'],
        medium=row['medium'],
        image_url=final_image_url,
        description=row['description'],
        credit=row['credit_line'],
        dimensions=row['dimensions'],
        department=department,
        url=row['url']
    )

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}

@app.get("/api/search", response_model=List[Artwork])
def search_artworks(
    request: Request, 
    q: str = Query(..., min_length=1, max_length=200),
    has_image: bool = Query(True, description="Only return artworks with images")
):
    """Search artworks using FTS5 full-text search with optional image filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Use FTS5 for better search performance and relevance
    # FTS5 automatically handles word stemming and relevance ranking
    fts_query = q.strip()
    
    if not fts_query:
        return []
    
    # Convert to OR query with prefix matching for better results
    # e.g., "two bird" becomes "two* OR bird*" to match "birds", "korean" matches "korea"
    search_terms = fts_query.split()
    fts_or_query = " OR ".join([f"{term}*" for term in search_terms])
    
    # Build advanced priority scoring for multi-word queries
    # Priority levels:
    #   1 = Exact phrase match ("ancient silence" as is)
    #   2 = All words present (any order)
    #   3 = First word exact match
    #   4 = Second word exact match (if exists)
    #   5 = Any word prefix match
    #   6 = Partial match
    
    priority_cases = []
    
    if len(search_terms) == 1:
        # Single word query - use original priority system
        term_lower = search_terms[0].lower()
        priority_cases.append(f"WHEN LOWER(a.title) LIKE '% {term_lower} %' OR LOWER(a.title) LIKE '{term_lower} %' OR LOWER(a.title) LIKE '% {term_lower}' OR LOWER(a.title) = '{term_lower}' THEN 1")
        priority_cases.append(f"WHEN LOWER(a.artist) LIKE '% {term_lower} %' OR LOWER(a.artist) LIKE '{term_lower} %' OR LOWER(a.artist) LIKE '% {term_lower}' OR LOWER(a.artist) = '{term_lower}' THEN 1")
        priority_cases.append(f"WHEN LOWER(a.title) LIKE '% {term_lower}%' OR LOWER(a.title) LIKE '{term_lower}%' THEN 2")
        priority_cases.append(f"WHEN LOWER(a.artist) LIKE '% {term_lower}%' OR LOWER(a.artist) LIKE '{term_lower}%' THEN 2")
    
    elif len(search_terms) == 2:
        # Two word query - advanced priority
        term1_lower = search_terms[0].lower()
        term2_lower = search_terms[1].lower()
        phrase = f"{term1_lower} {term2_lower}"
        
        # Priority 1: Exact phrase match
        priority_cases.append(f"WHEN LOWER(a.title) LIKE '%{phrase}%' OR LOWER(a.artist) LIKE '%{phrase}%' THEN 1")
        
        # Priority 2: Both words present (any order, as whole words)
        priority_cases.append(f"WHEN (LOWER(a.title) LIKE '% {term1_lower} %' OR LOWER(a.title) LIKE '{term1_lower} %' OR LOWER(a.title) LIKE '% {term1_lower}' OR LOWER(a.title) = '{term1_lower}') AND (LOWER(a.title) LIKE '% {term2_lower} %' OR LOWER(a.title) LIKE '{term2_lower} %' OR LOWER(a.title) LIKE '% {term2_lower}' OR LOWER(a.title) = '{term2_lower}') THEN 2")
        priority_cases.append(f"WHEN (LOWER(a.artist) LIKE '% {term1_lower} %' OR LOWER(a.artist) LIKE '{term1_lower} %' OR LOWER(a.artist) LIKE '% {term1_lower}' OR LOWER(a.artist) = '{term1_lower}') AND (LOWER(a.artist) LIKE '% {term2_lower} %' OR LOWER(a.artist) LIKE '{term2_lower} %' OR LOWER(a.artist) LIKE '% {term2_lower}' OR LOWER(a.artist) = '{term2_lower}') THEN 2")
        
        # Priority 3: First word exact match
        priority_cases.append(f"WHEN LOWER(a.title) LIKE '% {term1_lower} %' OR LOWER(a.title) LIKE '{term1_lower} %' OR LOWER(a.title) LIKE '% {term1_lower}' OR LOWER(a.title) = '{term1_lower}' THEN 3")
        priority_cases.append(f"WHEN LOWER(a.artist) LIKE '% {term1_lower} %' OR LOWER(a.artist) LIKE '{term1_lower} %' OR LOWER(a.artist) LIKE '% {term1_lower}' OR LOWER(a.artist) = '{term1_lower}' THEN 3")
        
        # Priority 4: Second word exact match
        priority_cases.append(f"WHEN LOWER(a.title) LIKE '% {term2_lower} %' OR LOWER(a.title) LIKE '{term2_lower} %' OR LOWER(a.title) LIKE '% {term2_lower}' OR LOWER(a.title) = '{term2_lower}' THEN 4")
        priority_cases.append(f"WHEN LOWER(a.artist) LIKE '% {term2_lower} %' OR LOWER(a.artist) LIKE '{term2_lower} %' OR LOWER(a.artist) LIKE '% {term2_lower}' OR LOWER(a.artist) = '{term2_lower}' THEN 4")
        
        # Priority 5: Prefix match
        priority_cases.append(f"WHEN LOWER(a.title) LIKE '{term1_lower}%' OR LOWER(a.title) LIKE '% {term1_lower}%' OR LOWER(a.title) LIKE '{term2_lower}%' OR LOWER(a.title) LIKE '% {term2_lower}%' THEN 5")
        priority_cases.append(f"WHEN LOWER(a.artist) LIKE '{term1_lower}%' OR LOWER(a.artist) LIKE '% {term1_lower}%' OR LOWER(a.artist) LIKE '{term2_lower}%' OR LOWER(a.artist) LIKE '% {term2_lower}%' THEN 5")
    
    else:
        # Three or more words - use general approach
        all_terms_lower = [t.lower() for t in search_terms]
        
        # Check if all words present
        all_words_conditions = []
        for term_lower in all_terms_lower:
            all_words_conditions.append(f"(LOWER(a.title) LIKE '% {term_lower} %' OR LOWER(a.title) LIKE '{term_lower} %' OR LOWER(a.title) LIKE '% {term_lower}' OR LOWER(a.title) = '{term_lower}')")
        priority_cases.append(f"WHEN {' AND '.join(all_words_conditions)} THEN 1")
        
        # First word match
        term1_lower = all_terms_lower[0]
        priority_cases.append(f"WHEN LOWER(a.title) LIKE '% {term1_lower} %' OR LOWER(a.title) LIKE '{term1_lower} %' OR LOWER(a.title) LIKE '% {term1_lower}' OR LOWER(a.title) = '{term1_lower}' THEN 2")
        
        # Any word match
        for term_lower in all_terms_lower[1:]:
            priority_cases.append(f"WHEN LOWER(a.title) LIKE '% {term_lower} %' OR LOWER(a.title) LIKE '{term_lower} %' OR LOWER(a.title) LIKE '% {term_lower}' OR LOWER(a.title) = '{term_lower}' THEN 3")
    
    priority_case = " ".join(priority_cases) if priority_cases else "ELSE 6"
    
    # Build FTS5 query with priority scoring
    sql = f"""
        SELECT a.*, 
               CASE {priority_case} ELSE 6 END as priority
        FROM artworks a
        INNER JOIN artworks_fts fts ON a.artwork_id = fts.artwork_id
        WHERE artworks_fts MATCH ?
    """
    
    # Add image filter if requested
    if has_image:
        sql += " AND (a.image_path IS NOT NULL OR a.thumbnail_path IS NOT NULL)"
    
    # Order by priority first (1=exact, 2=prefix, 3=contains), then FTS5 rank
    sql += " ORDER BY priority ASC, rank ASC LIMIT 100"
    
    try:
        cursor.execute(sql, (fts_or_query,))
        rows = cursor.fetchall()
        
        # If FTS5 returns very few results, also try LIKE search and combine
        if len(rows) < 5:
            search_terms = fts_query.split()
            conditions = []
            parameters = []
            
            for term in search_terms:
                term_pattern = f"%{term}%"
                conditions.append("""
                    (title LIKE ? OR artist LIKE ? OR description LIKE ? OR medium LIKE ? OR date LIKE ?)
                """)
                parameters.extend([term_pattern] * 5)
            
            query_condition = " OR ".join(conditions)
            like_sql = f"SELECT * FROM artworks WHERE {query_condition}"
            
            if has_image:
                like_sql += " AND (image_path IS NOT NULL OR thumbnail_path IS NOT NULL)"
            
            like_sql += " LIMIT 100"
            
            cursor.execute(like_sql, tuple(parameters))
            like_rows = cursor.fetchall()
            
            # Combine results and deduplicate by artwork_id
            seen_ids = {row[1] for row in rows}  # artwork_id is at index 1
            for row in like_rows:
                if row[1] not in seen_ids:
                    rows.append(row)
                    seen_ids.add(row[1])
                    
    except sqlite3.OperationalError:
        # Fallback to LIKE search if FTS5 query syntax is invalid
        search_terms = fts_query.split()
        conditions = []
        parameters = []
        
        for term in search_terms:
            term_pattern = f"%{term}%"
            conditions.append("""
                (title LIKE ? OR artist LIKE ? OR description LIKE ? OR medium LIKE ? OR date LIKE ?)
            """)
            parameters.extend([term_pattern] * 5)
        
        query_condition = " OR ".join(conditions)
        sql = f"SELECT * FROM artworks WHERE {query_condition}"
        
        if has_image:
            sql += " AND (image_path IS NOT NULL OR thumbnail_path IS NOT NULL)"
        
        sql += " LIMIT 100"
        
        cursor.execute(sql, tuple(parameters))
        rows = cursor.fetchall()
    
    conn.close()
    
    base_url = str(request.base_url).rstrip('/')
    results = [map_row_to_artwork(row, base_url) for row in rows]
    
    # Deduplicate by Title (normalized)
    unique_results = []
    seen_titles = set()
    
    for art in results:
        if art.title:
            norm_title = art.title.strip().lower()
            if norm_title not in seen_titles:
                unique_results.append(art)
                seen_titles.add(norm_title)
        else:
            # Include artworks without titles but dedupe by ID
            if art.id not in seen_titles:
                unique_results.append(art)
                seen_titles.add(art.id)
            
    return unique_results

@app.get("/api/random", response_model=List[Artwork])
def random_artworks(
    request: Request, 
    count: int = Query(10, ge=1, le=50),
    has_image: bool = Query(True, description="Only return artworks with images")
):
    """Return random artworks for 'I'm Feeling Lucky'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query with optional image filter
    sql = "SELECT * FROM artworks"
    if has_image:
        sql += " WHERE (image_path IS NOT NULL OR thumbnail_path IS NOT NULL)"
    sql += " ORDER BY RANDOM() LIMIT ?"
    
    # Fetch more than needed to account for duplicates we might filter out
    cursor.execute(sql, (count * 3,))
    rows = cursor.fetchall()
    conn.close()
    
    base_url = str(request.base_url).rstrip('/')
    results = [map_row_to_artwork(row, base_url) for row in rows]
    
    # Deduplicate by Title
    unique_results = []
    seen_titles = set()
    for art in results:
        if art.title:
            norm_title = art.title.strip().lower()
            if norm_title not in seen_titles:
                unique_results.append(art)
                seen_titles.add(norm_title)
            if len(unique_results) >= count:
                break
                
    return unique_results

@app.get("/api/artwork/{artwork_id}", response_model=Artwork)
def get_artwork(artwork_id: str, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM artworks WHERE artwork_id = ?", (artwork_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        base_url = str(request.base_url).rstrip('/')
        return map_row_to_artwork(row, base_url)
    raise HTTPException(status_code=404, detail="Artwork not found")

# Serve images if they exist locally (future proofing)
if os.path.exists(IMAGES_DIR):
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")
