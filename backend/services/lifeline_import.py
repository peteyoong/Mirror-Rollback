"""
Lifeline Import Service

Extracts timeline events from uploaded files (PPTX, PDF, Excel, CSV, Images).
Returns structured event candidates with confidence scores for the review UI.
"""

import re
import io
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Maximum events to return (Task 46: increased for larger imports)
MAX_EVENTS = 50

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    '.pptx': 'powerpoint',
    '.pdf': 'pdf',
    '.xlsx': 'excel',
    '.xls': 'excel',
    '.csv': 'csv',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.png': 'image',
}

# Category keywords for classification
CATEGORY_KEYWORDS = {
    'Career': [
        'job', 'work', 'career', 'promotion', 'hired', 'fired', 'laid off',
        'started working', 'joined', 'left', 'resigned', 'company', 'business',
        'founded', 'entrepreneur', 'startup', 'professional', 'manager', 'director',
        'executive', 'intern', 'graduate', 'degree', 'university', 'college',
        'studied', 'major', 'phd', 'masters', 'bachelor', 'certification'
    ],
    'Relationships': [
        'married', 'engaged', 'dating', 'met', 'fell in love', 'partner',
        'spouse', 'wife', 'husband', 'boyfriend', 'girlfriend', 'divorce',
        'separated', 'breakup', 'wedding', 'relationship', 'together',
        'proposed', 'anniversary', 'friendship', 'best friend'
    ],
    'Move': [
        'moved', 'relocated', 'immigrated', 'emigrated', 'travel', 'trip',
        'visited', 'settled', 'new city', 'new country', 'apartment',
        'house', 'home', 'living in', 'moved to', 'migration', 'abroad'
    ],
    'Family': [
        'born', 'baby', 'child', 'son', 'daughter', 'parent', 'mother',
        'father', 'sibling', 'brother', 'sister', 'family', 'pregnant',
        'adoption', 'adopted', 'grandparent', 'grandmother', 'grandfather'
    ],
    'Achievement': [
        'won', 'award', 'achievement', 'accomplished', 'success', 'milestone',
        'completed', 'finished', 'graduated', 'launched', 'published',
        'recognized', 'honor', 'prize', 'medal', 'champion', 'first'
    ],
    'Loss': [
        'died', 'death', 'passed away', 'lost', 'grief', 'funeral', 'cancer',
        'illness', 'tragedy', 'mourning', 'goodbye', 'passed', 'memorial'
    ],
    'Health': [
        'diagnosed', 'surgery', 'hospital', 'health', 'illness', 'recovery',
        'treatment', 'therapy', 'mental health', 'depression', 'anxiety',
        'accident', 'injury', 'rehabilitation', 'doctor', 'medical'
    ],
    'Identity': [
        'realized', 'discovered', 'identity', 'came out', 'transition',
        'spiritual', 'awakening', 'changed', 'transformation', 'crisis',
        'found myself', 'self-discovery', 'breakthrough', 'epiphany'
    ],
    'Money': [
        'money', 'financial', 'investment', 'savings', 'debt', 'bankrupt',
        'wealthy', 'income', 'salary', 'raise', 'bonus', 'bought', 'sold',
        'property', 'inheritance', 'lottery', 'stock', 'crypto'
    ],
    'Turning Point': [
        'turning point', 'changed everything', 'pivotal', 'crossroads',
        'decision', 'life-changing', 'defining moment', 'watershed',
        'breakthrough', 'new chapter', 'started fresh', 'new beginning'
    ],
}

# Year patterns for extraction
YEAR_PATTERNS = [
    # Explicit year patterns
    r'\b(19[5-9]\d|20[0-2]\d)\b',  # Years 1950-2029
    # Year with context
    r'(?:in|during|around|circa|year)\s*(19[5-9]\d|20[0-2]\d)',
    # Year ranges (take first year)
    r'(19[5-9]\d|20[0-2]\d)\s*[-–—]\s*(?:19[5-9]\d|20[0-2]\d)',
    # Age patterns: "at age 25" or "when I was 25"
    r'(?:at\s+)?age\s+(\d{1,2})',
    r'when\s+I\s+was\s+(\d{1,2})',
]

# Event indicator patterns
EVENT_PATTERNS = [
    # Year + description
    r'(19[5-9]\d|20[0-2]\d)\s*[-–—:]\s*(.+?)(?:\n|$)',
    r'(19[5-9]\d|20[0-2]\d)\s*[.]\s*(.+?)(?:\n|$)',
    # Bullet points with years
    r'[•\-*]\s*(19[5-9]\d|20[0-2]\d)\s*[-–—:.]?\s*(.+?)(?:\n|$)',
    # Numbered lists with years
    r'\d+[.)]\s*(19[5-9]\d|20[0-2]\d)\s*[-–—:.]?\s*(.+?)(?:\n|$)',
]

# Task 74: Enhanced patterns for PDF/PPTX content
SLIDE_EVENT_PATTERNS = [
    # Slide title with year: "[Slide N Title] 2018 - Started new job"
    r'\[Slide\s+\d+\s+Title\]\s*(19[5-9]\d|20[0-2]\d)\s*[-–—:.]?\s*(.+?)(?:\n|$)',
    # Year followed by title text
    r'(19[5-9]\d|20[0-2]\d)\s*[-–—:.]\s*([A-Z][^.\n]{5,80})',
    # Life event phrases with year
    r'(?:born|graduated|married|moved|started|joined|left|died|won)\s+(?:in\s+)?(19[5-9]\d|20[0-2]\d)',
    # "In 2005, ..." pattern
    r'[Ii]n\s+(19[5-9]\d|20[0-2]\d)[,.]?\s+(.+?)(?:\n|$)',
    # Year at end: "Got my first job (1998)"
    r'([A-Z][^.\n]{5,80})\s*\((19[5-9]\d|20[0-2]\d)\)',
    # "Since 2010" or "From 2005" patterns
    r'(?:since|from)\s+(19[5-9]\d|20[0-2]\d)[,.]?\s*(.{0,80})',
]

# Junk text patterns to filter out
JUNK_PATTERNS = [
    r'^page\s*\d+',
    r'^\d+\s*$',  # Just numbers
    r'^copyright',
    r'^all rights reserved',
    r'^confidential',
    r'^\s*•\s*$',  # Just bullet
    r'^www\.',
    r'^http',
    r'@.*\.com',  # Email addresses
    r'^\s*[-–—]\s*$',  # Just dashes
]


# =============================================================================
# FILE EXTRACTION FUNCTIONS
# =============================================================================

def extract_text_from_pptx(file_bytes: bytes) -> str:
    """
    Extract text from PowerPoint file with enhanced timeline detection.
    
    Task 74: Enhanced extraction for:
    - Slide titles (often contain key life events)
    - Bullet points with year + description patterns
    - Text boxes with timeline content
    - Tables with year/event columns
    - Notes sections
    """
    try:
        from pptx import Presentation
        from pptx.util import Inches
        
        prs = Presentation(io.BytesIO(file_bytes))
        text_parts = []
        slide_events = []  # Structured events with context
        
        logger.info(f"[LifelineImport/PPTX] Processing {len(prs.slides)} slides")
        
        for slide_num, slide in enumerate(prs.slides, 1):
            slide_title = None
            slide_bullets = []
            slide_text = []
            
            for shape in slide.shapes:
                # Extract title separately (high-value content)
                if shape.has_text_frame:
                    if hasattr(shape, 'is_placeholder') and shape.is_placeholder:
                        if hasattr(shape, 'placeholder_format'):
                            pf = shape.placeholder_format
                            # Title placeholder types: 1 (title), 3 (center title)
                            if hasattr(pf, 'type') and pf.type in [1, 3]:
                                slide_title = shape.text.strip()
                    
                    # Extract all text with paragraph structure
                    for para in shape.text_frame.paragraphs:
                        para_text = para.text.strip()
                        if para_text:
                            # Detect if this is a bullet point (has indent level)
                            if para.level > 0 or (hasattr(para, 'bullet') and para.bullet):
                                slide_bullets.append(para_text)
                            else:
                                slide_text.append(para_text)
                
                # Extract from tables (common in timelines)
                if shape.has_table:
                    table = shape.table
                    for row_idx, row in enumerate(table.rows):
                        row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if row_cells:
                            # Try to identify year + description pattern in table
                            row_text = " | ".join(row_cells)
                            slide_text.append(f"[Table row] {row_text}")
            
            # Build slide output with structure
            slide_output = []
            if slide_title:
                slide_output.append(f"[Slide {slide_num} Title] {slide_title}")
                logger.debug(f"[LifelineImport/PPTX] Slide {slide_num} title: {slide_title[:50]}...")
            
            # Add non-bullet text
            for text in slide_text:
                if text and text != slide_title:
                    slide_output.append(text)
            
            # Add bullet points with marker
            for bullet in slide_bullets:
                slide_output.append(f"• {bullet}")
            
            if slide_output:
                text_parts.append("\n".join(slide_output))
            
            # Extract speaker notes (often contain additional context)
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes_text = slide.notes_slide.notes_text_frame.text.strip()
                if notes_text and len(notes_text) > 10:
                    text_parts.append(f"[Slide {slide_num} Notes] {notes_text}")
        
        result = "\n\n".join(text_parts)
        logger.info(f"[LifelineImport/PPTX] Extracted {len(result)} chars from {len(prs.slides)} slides")
        logger.debug(f"[LifelineImport/PPTX] Sample text: {result[:500]}...")
        
        return result
        
    except ImportError:
        logger.error("[LifelineImport/PPTX] python-pptx not installed")
        raise ValueError("PowerPoint processing not available. Please install python-pptx.")
    except Exception as e:
        logger.error(f"[LifelineImport/PPTX] Extraction failed: {e}")
        raise ValueError(f"Failed to extract text from PowerPoint: {str(e)}")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF file with enhanced timeline detection.
    
    Task 74: Enhanced extraction for:
    - Page-by-page text with structure preservation
    - Table detection for timeline formats
    - Year + event patterns in various layouts
    - Visual timeline detection (text boxes, annotations)
    - Filtering of headers/footers/page numbers
    """
    try:
        import pdfplumber
        
        text_parts = []
        all_tables = []
        total_chars = 0
        
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            logger.info(f"[LifelineImport/PDF] Processing {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_content = []
                
                # Extract main text
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    # Clean the text - remove common page artifacts
                    clean_lines = []
                    for line in page_text.split('\n'):
                        line = line.strip()
                        # Skip likely headers/footers/page numbers
                        if _is_pdf_junk_line(line, page_num, len(pdf.pages)):
                            logger.debug(f"[LifelineImport/PDF] Filtered junk line: {line[:50]}")
                            continue
                        if line:
                            clean_lines.append(line)
                    
                    if clean_lines:
                        page_content.append("\n".join(clean_lines))
                
                # Extract tables (common in timelines)
                tables = page.extract_tables()
                if tables:
                    for table_idx, table in enumerate(tables):
                        if table:
                            table_text = _process_pdf_table(table, page_num, table_idx)
                            if table_text:
                                page_content.append(table_text)
                                all_tables.append((page_num, table_idx))
                
                if page_content:
                    combined = f"[Page {page_num}]\n" + "\n".join(page_content)
                    text_parts.append(combined)
                    total_chars += len(combined)
        
        result = "\n\n".join(text_parts)
        logger.info(f"[LifelineImport/PDF] Extracted {total_chars} chars from {len(pdf.pages)} pages, {len(all_tables)} tables")
        logger.debug(f"[LifelineImport/PDF] Sample text: {result[:500]}...")
        
        return result
        
    except ImportError:
        logger.error("[LifelineImport/PDF] pdfplumber not installed")
        raise ValueError("PDF processing not available. Please install pdfplumber.")
    except Exception as e:
        logger.error(f"[LifelineImport/PDF] Extraction failed: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def _is_pdf_junk_line(line: str, page_num: int, total_pages: int) -> bool:
    """
    Detect and filter PDF junk lines (page numbers, headers, footers).
    
    Task 74: Reduces noise in extracted text to improve event detection quality.
    """
    line_lower = line.lower().strip()
    
    # Empty or very short lines
    if len(line) < 3:
        return True
    
    # Pure page number patterns
    if re.match(r'^[\d\s\-/]+$', line) and len(line) < 10:
        return True
    
    # Page N of M patterns
    if re.match(r'^page\s*\d+\s*(of\s*\d+)?$', line_lower):
        return True
    
    # Just the page number
    if line.strip() == str(page_num):
        return True
    
    # Copyright/footer patterns
    if any(marker in line_lower for marker in ['©', 'copyright', 'all rights reserved', 'confidential']):
        return True
    
    # Common document headers/footers
    if any(marker in line_lower for marker in ['table of contents', 'appendix', 'references']):
        # Allow these as they might contain dates
        return False
    
    # Purely numeric (not years)
    if line.replace(' ', '').replace('-', '').replace('/', '').isdigit():
        # Could be a date - check if it looks like a year
        year_match = re.search(r'\b(19[5-9]\d|20[0-2]\d)\b', line)
        if not year_match:
            return True
    
    return False


def _process_pdf_table(table: List[List[str]], page_num: int, table_idx: int) -> str:
    """
    Process a PDF table and extract structured timeline data.
    
    Task 74: Handles various table formats:
    - Year | Event columns
    - Date | Description | Category columns
    - Multi-column timelines
    """
    if not table or len(table) < 2:
        return ""
    
    output_lines = []
    year_col_idx = None
    header_row = table[0] if table else []
    
    # Try to detect year column from headers
    for idx, cell in enumerate(header_row):
        if cell:
            cell_lower = str(cell).lower().strip()
            if cell_lower in ['year', 'date', 'when', 'time', 'period']:
                year_col_idx = idx
                break
    
    logger.debug(f"[LifelineImport/PDF] Table on page {page_num}: {len(table)} rows, year_col: {year_col_idx}")
    
    # Process table rows
    for row_idx, row in enumerate(table):
        if not row:
            continue
        
        # Clean cells
        cells = [str(cell).strip() if cell else '' for cell in row]
        
        # Skip empty rows
        if not any(cells):
            continue
        
        # Try to extract year from row
        row_year = None
        row_text_parts = []
        
        for cell_idx, cell in enumerate(cells):
            if not cell:
                continue
            
            # Check if this cell contains a year
            year_match = re.search(r'\b(19[5-9]\d|20[0-2]\d)\b', cell)
            if year_match and not row_year:
                row_year = year_match.group(1)
                # If cell is just the year, don't add to text
                remaining = re.sub(r'\b(19[5-9]\d|20[0-2]\d)\b', '', cell).strip()
                if remaining and len(remaining) > 3:
                    row_text_parts.append(remaining)
            else:
                # Add non-year content
                if len(cell) > 2 and not cell.replace('.', '').replace(',', '').isdigit():
                    row_text_parts.append(cell)
        
        # Build output line
        if row_text_parts:
            row_text = " - ".join(row_text_parts)
            if row_year:
                output_lines.append(f"{row_year} - {row_text}")
            elif len(row_text) > 10:
                output_lines.append(row_text)
    
    if output_lines:
        return f"[Table {table_idx + 1}]\n" + "\n".join(output_lines)
    return ""


def extract_text_from_excel(file_bytes: bytes) -> str:
    """
    Extract text from Excel file with improved parsing for visual timelines.
    
    Task 46: Enhanced to handle:
    - Multiple sheets (Personal, Career, Combined, etc.)
    - Visual formatting where years are scattered
    - Merged cells and irregular layouts
    - Year + description patterns
    """
    try:
        import pandas as pd
        
        xlsx = pd.ExcelFile(io.BytesIO(file_bytes))
        all_events = []
        sheets_scanned = 0
        total_rows_processed = 0
        
        logger.info(f"[LifelineImport/Excel] Found {len(xlsx.sheet_names)} sheets: {xlsx.sheet_names}")
        
        for sheet_name in xlsx.sheet_names:
            sheets_scanned += 1
            try:
                # Read with header=None to handle sheets without proper headers
                df = pd.read_excel(xlsx, sheet_name=sheet_name, header=None)
                
                # Also try with headers for structured data
                df_with_headers = pd.read_excel(xlsx, sheet_name=sheet_name)
                
                logger.info(f"[LifelineImport/Excel] Sheet '{sheet_name}': {len(df)} rows, {len(df.columns)} cols")
                
                # Method 1: Scan for year patterns in all cells
                sheet_events = _extract_events_from_excel_sheet(df, sheet_name)
                all_events.extend(sheet_events)
                total_rows_processed += len(df)
                
                # Method 2: Try structured extraction if there's a year column
                structured_events = _extract_events_from_structured_excel(df_with_headers, sheet_name)
                all_events.extend(structured_events)
                
            except Exception as sheet_error:
                logger.warning(f"[LifelineImport/Excel] Error reading sheet '{sheet_name}': {sheet_error}")
                continue
        
        logger.info(f"[LifelineImport/Excel] Scanned {sheets_scanned} sheets, {total_rows_processed} rows, found {len(all_events)} raw events")
        
        # Deduplicate events by year+content
        seen = set()
        unique_events = []
        for event in all_events:
            key = f"{event.get('year')}:{event.get('text', '')[:30].lower()}"
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        # Convert to text format for downstream processing
        text_lines = []
        for event in unique_events:
            year = event.get('year')
            text = event.get('text', '').strip()
            if year and text:
                text_lines.append(f"{year} - {text}")
            elif text and len(text) > 10:
                text_lines.append(text)
        
        result = "\n".join(text_lines)
        logger.info(f"[LifelineImport/Excel] Final extracted text ({len(result)} chars), {len(unique_events)} unique events")
        
        return result
        
    except Exception as e:
        logger.error(f"[LifelineImport/Excel] Excel extraction failed: {e}")
        raise ValueError(f"Failed to extract text from Excel: {str(e)}")


def _extract_events_from_excel_sheet(df, sheet_name: str) -> List[Dict[str, Any]]:
    """
    Extract events by scanning all cells for year patterns.
    Handles visually formatted timelines where years and descriptions
    may be in adjacent cells.
    
    CRITICAL: Only accepts 4-digit years (1950-2030), NOT ages like 25, 45, etc.
    """
    import pandas as pd
    
    events = []
    # Strict 4-digit year patterns only
    year_pattern = re.compile(r'^(19[5-9]\d|20[0-2]\d)$')
    year_with_text_pattern = re.compile(r'^(19[5-9]\d|20[0-2]\d)\s*[-–—:.]?\s*(.+)$')
    
    rows_with_years = 0
    
    for row_idx in range(len(df)):
        row = df.iloc[row_idx]
        row_year = None
        row_texts = []
        
        for col_idx, cell in enumerate(row):
            if pd.isna(cell):
                continue
            
            cell_str = str(cell).strip()
            if not cell_str:
                continue
            
            # Check if cell is just a 4-digit year (not an age)
            year_match = year_pattern.match(cell_str)
            if year_match:
                potential_year = int(year_match.group(1))
                # Validate it's a real year, not something that looks like one
                if 1950 <= potential_year <= 2030:
                    row_year = potential_year
                continue
            
            # Check if cell contains "year - description" format
            year_text_match = year_with_text_pattern.match(cell_str)
            if year_text_match:
                potential_year = int(year_text_match.group(1))
                if 1950 <= potential_year <= 2030:
                    row_year = potential_year
                    remaining_text = year_text_match.group(2).strip()
                    if remaining_text:
                        row_texts.append(remaining_text)
                continue
            
            # Regular text (not a year) - add to row texts
            # Skip very short cells, purely numeric cells, and cells that look like ages
            if len(cell_str) > 2:
                # Skip if it's just a number (could be age, score, etc.)
                if cell_str.replace('.', '').replace(',', '').replace('-', '').isdigit():
                    continue
                row_texts.append(cell_str)
        
        # If we found a valid 4-digit year and some text, create an event
        if row_year and row_texts:
            rows_with_years += 1
            combined_text = " ".join(row_texts)
            # Clean up the text
            combined_text = re.sub(r'\s+', ' ', combined_text).strip()
            
            if len(combined_text) >= 3:
                events.append({
                    'year': row_year,
                    'text': combined_text,
                    'source': f'sheet:{sheet_name}:row:{row_idx}'
                })
                logger.debug(f"[LifelineImport/Excel] Found event: {row_year} - {combined_text[:50]}...")
    
    logger.info(f"[LifelineImport/Excel] Sheet '{sheet_name}': {rows_with_years} rows with years, {len(events)} events extracted")
    return events


def _extract_events_from_structured_excel(df, sheet_name: str) -> List[Dict[str, Any]]:
    """
    Extract events from Excel with structured columns (Year, Event, Description, etc.)
    
    CRITICAL: Distinguishes between 'Year' columns (1950-2030) and 'Age' columns (0-100).
    Only extracts events with valid 4-digit years.
    """
    import pandas as pd
    
    events = []
    
    # Try to detect year column (NOT age column)
    year_col = None
    age_col = None
    text_cols = []
    
    for col in df.columns:
        col_name = str(col).lower().strip()
        
        # Explicitly check for age columns to EXCLUDE them
        if col_name in ['age', 'age at time', 'your age']:
            age_col = col
            logger.info(f"[LifelineImport/Excel] Sheet '{sheet_name}': Detected AGE column '{col}' - will NOT use as year")
            continue
        
        # Check if this is a year column by name
        if col_name in ['year', 'date', 'when', 'time']:
            year_col = col
        elif 'year' in col_name and 'age' not in col_name:
            year_col = col
        # Check if column values look like 4-digit years (NOT ages)
        elif year_col is None:
            try:
                sample = df[col].dropna().head(10)
                if len(sample) > 0:
                    # Check if ALL values are 4-digit years in valid range
                    valid_years = []
                    for v in sample:
                        try:
                            val = int(float(v))
                            if 1950 <= val <= 2030:
                                valid_years.append(val)
                        except (ValueError, TypeError):
                            pass
                    
                    # Only use as year column if majority are valid 4-digit years
                    if len(valid_years) >= len(sample) * 0.5 and len(valid_years) > 0:
                        # Double-check it's not ages (ages are typically < 100)
                        if all(v >= 1950 for v in valid_years):
                            year_col = col
                            logger.info(f"[LifelineImport/Excel] Sheet '{sheet_name}': Detected YEAR column by values: '{col}'")
            except (ValueError, TypeError):
                pass
        
        # Identify text columns (exclude year, age, and numeric columns)
        if col_name not in ['year', 'date', 'when', 'time', 'age'] and not str(col).startswith('Unnamed'):
            text_cols.append(col)
    
    if year_col is None:
        logger.debug(f"[LifelineImport/Excel] Sheet '{sheet_name}': No valid YEAR column detected (age columns excluded)")
        return events
    
    logger.info(f"[LifelineImport/Excel] Sheet '{sheet_name}': Using year column '{year_col}', text columns: {text_cols[:3]}")
    
    for idx, row in df.iterrows():
        try:
            year_val = row[year_col]
            if pd.isna(year_val):
                continue
            
            # Parse year - must be 4-digit year
            year = None
            try:
                year = int(float(year_val))
                # Strict validation: must be 4-digit year, not age
                if not (1950 <= year <= 2030):
                    continue
            except (ValueError, TypeError):
                continue
            
            # Collect text from other columns
            texts = []
            for col in text_cols:
                val = row.get(col)
                if pd.notna(val):
                    val_str = str(val).strip()
                    # Skip empty, numeric-only values, and very short strings
                    if val_str and len(val_str) > 2:
                        if not val_str.replace('.', '').replace(',', '').replace('-', '').isdigit():
                            texts.append(val_str)
            
            if texts:
                combined_text = " - ".join(texts)
                events.append({
                    'year': year,
                    'text': combined_text,
                    'source': f'structured:{sheet_name}:row:{idx}'
                })
        except Exception as row_error:
            continue
    
    logger.info(f"[LifelineImport/Excel] Sheet '{sheet_name}': {len(events)} structured events with valid years")
    return events


def extract_text_from_csv(file_bytes: bytes) -> str:
    """Extract text from CSV file."""
    try:
        import pandas as pd
        
        # Try different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Unable to decode CSV with supported encodings")
        
        text_parts = []
        
        # Detect if there's a year column
        year_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if col_lower in ['year', 'date', 'when', 'time']:
                year_col = col
                break
            # Check if column values look like years
            try:
                sample = df[col].dropna().head(5)
                if all(1900 <= int(v) <= 2100 for v in sample if str(v).isdigit()):
                    year_col = col
                    break
            except (ValueError, TypeError):
                continue
        
        logger.info(f"[LifelineImport] CSV year_col detected: {year_col}")
        
        # Add row data with year prefix if found
        for idx, row in df.iterrows():
            row_parts = []
            
            # Extract year first if we have a year column - format it properly for regex matching
            if year_col is not None and pd.notna(row.get(year_col)):
                year_value = str(int(row[year_col])) if isinstance(row[year_col], (int, float)) else str(row[year_col]).strip()
                if year_value.isdigit() and 1900 <= int(year_value) <= 2100:
                    row_parts.append(f"{year_value} -")
            
            # Add other values
            for col in df.columns:
                if col == year_col:
                    continue
                val = row.get(col)
                if pd.notna(val) and str(val).strip():
                    row_parts.append(str(val).strip())
            
            if row_parts:
                row_text = " ".join(row_parts)
                text_parts.append(row_text)
                logger.debug(f"[LifelineImport] CSV row: {row_text}")
        
        result = "\n".join(text_parts)
        logger.info(f"[LifelineImport] CSV extracted text ({len(result)} chars): {result[:500]}...")
        return result
    except Exception as e:
        logger.error(f"[LifelineImport] CSV extraction failed: {e}")
        raise ValueError(f"Failed to extract text from CSV: {str(e)}")


def extract_text_from_image(file_bytes: bytes) -> str:
    """Extract text from image using OCR."""
    try:
        import pytesseract
        from PIL import Image
        
        # Open image
        image = Image.open(io.BytesIO(file_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract text using OCR
        text = pytesseract.image_to_string(image)
        
        if not text.strip():
            raise ValueError("No text could be extracted from the image")
        
        return text.strip()
    except ImportError:
        logger.error("[LifelineImport] pytesseract not properly installed")
        raise ValueError("OCR service not available. Please try a different file format.")
    except Exception as e:
        logger.error(f"[LifelineImport] Image OCR failed: {e}")
        raise ValueError(f"Failed to extract text from image: {str(e)}")


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract text from file based on extension."""
    import os
    
    ext = os.path.splitext(filename.lower())[1]
    
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file format: {ext}")
    
    file_type = SUPPORTED_EXTENSIONS[ext]
    
    if file_type == 'powerpoint':
        return extract_text_from_pptx(file_bytes)
    elif file_type == 'pdf':
        return extract_text_from_pdf(file_bytes)
    elif file_type == 'excel':
        return extract_text_from_excel(file_bytes)
    elif file_type == 'csv':
        return extract_text_from_csv(file_bytes)
    elif file_type == 'image':
        return extract_text_from_image(file_bytes)
    else:
        raise ValueError(f"Unknown file type: {file_type}")


# =============================================================================
# EVENT EXTRACTION FUNCTIONS
# =============================================================================

def classify_event_category(text: str) -> Tuple[str, float]:
    """
    Classify event into a category based on keywords.
    Returns (category, keyword_score).
    """
    text_lower = text.lower()
    
    best_category = 'Other'
    best_score = 0
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > best_score:
            best_score = matches
            best_category = category
    
    # Normalize score (0-1)
    keyword_score = min(best_score / 3.0, 1.0)
    
    return best_category, keyword_score


def extract_year_from_text(text: str, birth_year: Optional[int] = None) -> Optional[int]:
    """
    Extract year from text using various patterns.
    """
    # Try explicit year patterns first
    for pattern in YEAR_PATTERNS[:3]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            if 1950 <= year <= datetime.now().year:
                return year
    
    # Try age patterns if birth_year is provided
    if birth_year:
        for pattern in YEAR_PATTERNS[3:]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 0 <= age <= 100:
                    year = birth_year + age
                    if 1950 <= year <= datetime.now().year:
                        return year
    
    return None


def calculate_confidence(
    has_year: bool,
    title_length: int,
    description_length: int,
    keyword_score: float,
    has_specific_context: bool
) -> float:
    """
    Calculate confidence score for an extracted event.
    """
    confidence = 0.0
    
    # Year presence is a strong signal
    if has_year:
        confidence += 0.35
    
    # Title quality
    if title_length >= 5:
        confidence += 0.15
    if title_length >= 15:
        confidence += 0.10
    
    # Description quality
    if description_length >= 20:
        confidence += 0.10
    if description_length >= 50:
        confidence += 0.05
    
    # Keyword match score
    confidence += keyword_score * 0.20
    
    # Specific context (dates, names, places)
    if has_specific_context:
        confidence += 0.05
    
    return min(round(confidence, 2), 1.0)


def has_specific_context(text: str) -> bool:
    """Check if text has specific contextual details."""
    # Check for proper nouns (capitalized words not at sentence start)
    proper_nouns = re.findall(r'(?<=[.!?]\s)[A-Z][a-z]+|(?<=\s)[A-Z][a-z]+', text)
    
    # Check for specific patterns
    has_numbers = bool(re.search(r'\b\d+\b', text))
    has_locations = bool(re.search(r'(?:in|at|to)\s+[A-Z][a-z]+', text))
    has_names = len(proper_nouns) > 1
    
    return has_numbers or has_locations or has_names


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters
    text = re.sub(r'[^\w\s\-.,;:!?\'\"()\[\]]', '', text)
    return text.strip()


def create_title_from_text(text: str, max_length: int = 60) -> str:
    """Create a concise title from text."""
    # Clean the text
    text = clean_text(text)
    
    # Remove year prefix if present (e.g., "2018 - " or "2018: ")
    text = re.sub(r'^\d{4}\s*[-–—:.]?\s*', '', text)
    
    # If short enough, use as is
    if len(text) <= max_length:
        return text
    
    # Try to find a natural break point
    truncated = text[:max_length]
    
    # Look for sentence boundary
    for sep in ['. ', '! ', '? ', ' - ', ', ']:
        if sep in truncated:
            truncated = truncated.rsplit(sep, 1)[0] + sep.strip()
            break
    else:
        # Just cut at word boundary
        truncated = truncated.rsplit(' ', 1)[0] + '...'
    
    return truncated


def extract_events_from_structured_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract events from structured text (year - description format).
    """
    events = []
    
    # Try each event pattern
    for pattern in EVENT_PATTERNS:
        matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            if len(match) >= 2:
                year_str, description = match[0], match[1]
                try:
                    year = int(year_str)
                    if 1950 <= year <= datetime.now().year:
                        description = clean_text(description)
                        if len(description) >= 5:
                            events.append({
                                'year': year,
                                'raw_text': description,
                                'source': 'structured'
                            })
                except ValueError:
                    continue
    
    return events


def extract_events_from_sentences(text: str, birth_year: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract events from natural language sentences.
    """
    events = []
    
    # Split into sentences
    sentences = re.split(r'[.!?\n]+', text)
    
    for sentence in sentences:
        sentence = clean_text(sentence)
        
        if len(sentence) < 10:
            continue
        
        # Try to extract year
        year = extract_year_from_text(sentence, birth_year)
        
        if year:
            # Check if this sentence describes an event
            category, keyword_score = classify_event_category(sentence)
            
            # Only include if we have some keyword match or it looks like an event
            if keyword_score > 0 or any(
                indicator in sentence.lower() 
                for indicator in ['started', 'began', 'moved', 'met', 'married', 'born', 'died', 'graduated', 'joined', 'left', 'won', 'lost', 'bought', 'sold']
            ):
                events.append({
                    'year': year,
                    'raw_text': sentence,
                    'source': 'sentence'
                })
    
    return events


def extract_lifeline_events(
    text: str, 
    birth_year: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Main function to extract lifeline events from text.
    
    Returns list of event candidates with:
    - year: int or None
    - title: str
    - description: str
    - category: str
    - confidence: float (0-1)
    """
    if not text or len(text.strip()) < 20:
        return []
    
    logger.info(f"[LifelineImport] Extracting events from {len(text)} chars of text")
    
    # Collect raw events from different extraction methods
    raw_events = []
    
    # Method 1: Structured text extraction
    structured_events = extract_events_from_structured_text(text)
    raw_events.extend(structured_events)
    logger.info(f"[LifelineImport] Found {len(structured_events)} structured events")
    
    # Method 2: Sentence-based extraction
    sentence_events = extract_events_from_sentences(text, birth_year)
    raw_events.extend(sentence_events)
    logger.info(f"[LifelineImport] Found {len(sentence_events)} sentence events")
    
    # Deduplicate and process events
    seen_hashes = set()
    processed_events = []
    
    for raw_event in raw_events:
        raw_text = raw_event['raw_text']
        year = raw_event.get('year')
        
        # Normalize text for deduplication - remove year prefix and extra whitespace
        normalized_text = re.sub(r'^\d{4}\s*[-–—:.]?\s*', '', raw_text.lower())
        normalized_text = re.sub(r'\s+', ' ', normalized_text).strip()[:40]
        
        # Create hash for deduplication using normalized text
        event_hash = hashlib.md5(f"{year}:{normalized_text}".encode()).hexdigest()[:8]
        if event_hash in seen_hashes:
            continue
        seen_hashes.add(event_hash)
        
        # Classify category
        category, keyword_score = classify_event_category(raw_text)
        
        # Create title
        title = create_title_from_text(raw_text)
        
        # Check for specific context
        has_context = has_specific_context(raw_text)
        
        # Calculate confidence
        confidence = calculate_confidence(
            has_year=year is not None,
            title_length=len(title),
            description_length=len(raw_text),
            keyword_score=keyword_score,
            has_specific_context=has_context
        )
        
        # Create event object
        event = {
            'year': year,
            'title': title,
            'description': raw_text,
            'category': category,
            'confidence': confidence,
        }
        
        processed_events.append(event)
    
    # Sort by confidence (descending) and limit
    processed_events.sort(key=lambda e: (e['confidence'], e.get('year') or 0), reverse=True)
    
    # Return top events
    result = processed_events[:MAX_EVENTS]
    logger.info(f"[LifelineImport] Returning {len(result)} events (from {len(processed_events)} candidates)")
    
    return result


# =============================================================================
# MAIN IMPORT FUNCTION
# =============================================================================

async def process_lifeline_import(
    file_bytes: bytes,
    filename: str,
    user_id: str,
    birth_year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main entry point for processing lifeline imports.
    
    Args:
        file_bytes: Raw file content
        filename: Original filename
        user_id: User ID for logging
        birth_year: Optional birth year for age-based detection
    
    Returns:
        Dict with 'events' list and optional 'message'
    """
    import os
    
    logger.info(f"[LifelineImport] Processing file '{filename}' for user {user_id}")
    
    # Validate file size
    if len(file_bytes) > MAX_FILE_SIZE:
        return {
            'events': [],
            'message': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.',
            'success': False
        }
    
    # Validate file extension
    ext = os.path.splitext(filename.lower())[1]
    if ext not in SUPPORTED_EXTENSIONS:
        return {
            'events': [],
            'message': f'Unsupported file format. Supported formats: {", ".join(SUPPORTED_EXTENSIONS.keys())}',
            'success': False
        }
    
    try:
        # Extract text from file
        text = extract_text_from_file(file_bytes, filename)
        logger.info(f"[LifelineImport] Extracted {len(text)} characters from {filename}")
        
        if not text or len(text.strip()) < 20:
            return {
                'events': [],
                'message': 'The file appears to be empty or contains very little text.',
                'success': False
            }
        
        # Extract events
        events = extract_lifeline_events(text, birth_year)
        
        if not events:
            return {
                'events': [],
                'message': "We couldn't confidently extract timeline events from this file. Try a file with clear dates and life events.",
                'success': False
            }
        
        # Add IDs to events
        for idx, event in enumerate(events):
            event['id'] = f"import-{user_id[:8]}-{idx}"
        
        return {
            'events': events,
            'message': f'Successfully extracted {len(events)} events.',
            'success': True
        }
        
    except ValueError as e:
        logger.warning(f"[LifelineImport] Validation error: {e}")
        return {
            'events': [],
            'message': str(e),
            'success': False
        }
    except Exception as e:
        logger.error(f"[LifelineImport] Unexpected error: {e}")
        return {
            'events': [],
            'message': 'An unexpected error occurred while processing the file.',
            'success': False
        }
