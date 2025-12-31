import sqlite3
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI()

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

# Database Config
DB_PATH = "../data/artworks.db"

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
        local_image_path = os.path.join("../data/images", image_filename)
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
def search_artworks(request: Request, q: str = Query(..., min_length=1)):
    """Search by title or artist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    search_terms = q.split()
    if not search_terms:
        return []

    conditions = []
    parameters = []
    
    for term in search_terms:
        term_pattern = f"%{term}%"
        # For each term, check if it appears in any of the fields
        conditions.append("""
            (title LIKE ? OR artist LIKE ? OR description LIKE ? OR medium LIKE ? OR date LIKE ?)
        """)
        parameters.extend([term_pattern] * 5)
    
    # helper for OR logic: finding entries that match ANY of the search terms
    # To make it stricter (AND), change " OR " to " AND " below
    query_condition = " OR ".join(conditions)

    sql = f"SELECT * FROM artworks WHERE {query_condition}"
    
    cursor.execute(sql, tuple(parameters))
    rows = cursor.fetchall()
    conn.close()
    
    base_url = str(request.base_url).rstrip('/')
    results = [map_row_to_artwork(row, base_url) for row in rows]
    
    # Deduplicate by Title (normalized)
    unique_results = []
    seen_titles = set()
    
    for art in results:
        # Normalize title for de-dupe (remove whitespace, lowercase)
        # Fallback to ID if title is None, though your model says title is Optional
        if art.title:
            norm_title = art.title.strip().lower()
            if norm_title not in seen_titles:
                unique_results.append(art)
                seen_titles.add(norm_title)
        else:
             # If no title, maybe allow it or dedupe by ID? 
             # Let's assume title is critical for this app.
             pass
            
    return unique_results

@app.get("/api/random", response_model=List[Artwork])
def random_artworks(request: Request, count: int = 10):
    """Return random artworks for 'I'm Feeling Lucky'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch more than needed to account for duplicates we might filter out
    cursor.execute("SELECT * FROM artworks ORDER BY RANDOM() LIMIT ?", (count * 3,))
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
if os.path.exists("../data/images"):
    app.mount("/images", StaticFiles(directory="../data/images"), name="images")
