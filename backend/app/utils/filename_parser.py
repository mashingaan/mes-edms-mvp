import re
from typing import Dict, Optional


def parse_filename(filename: str) -> Dict[str, Optional[str]]:
    """
    Parse filename to extract section_code, part_number, and name.
    
    Returns:
        Dict with keys: section_code, part_number, name
        - section_code: Optional[str] - e.g., "БНС.КМД"
        - part_number: Optional[str] - e.g., "123.456.789.001"
        - name: str - always non-empty, fallback to filename without extension
    
    Examples:
        - "БНС.КМД.123.456.789.001 Корпус.pdf" -> {"section_code": "БНС.КМД", "part_number": "123.456.789.001", "name": "Корпус"}
        - "БНС.ТХ.24. Ротор сборка.pdf" -> {"section_code": "БНС.ТХ", "part_number": "24", "name": "Ротор сборка"}
        - "Документ без кода.pdf" -> {"section_code": None, "part_number": None, "name": "Документ без кода"}
        - "random_file_name.pdf" -> {"section_code": None, "part_number": None, "name": "random_file_name"}
    """
    result: Dict[str, Optional[str]] = {
        "section_code": None,
        "part_number": None,
        "name": ""
    }
    
    try:
        # Remove extension (.pdf, .PDF)
        name_without_ext = filename
        if filename.lower().endswith('.pdf'):
            name_without_ext = filename[:-4]
        
        remaining = name_without_ext.strip()
        
        # Try to detect section code: match pattern like "БНС.КМД" or "БНС.ТХ" at start
        # Pattern: ^([А-ЯA-Z0-9]+\.[А-ЯA-Z0-9]+)\.
        section_pattern = r'^([А-ЯA-Z0-9]+\.[А-ЯA-Z0-9]+)\.'
        section_match = re.match(section_pattern, remaining)
        
        if section_match:
            result["section_code"] = section_match.group(1)
            remaining = remaining[section_match.end():].strip()
        
        # Try to extract part_number: look for decimal pattern like "123.456.789.001"
        # Pattern: (\d{2,3}\.\d{3}\.\d{3}\.\d{3})
        part_number_pattern = r'^(\d{2,3}\.\d{3}\.\d{3}\.\d{3})\s*(.*)$'
        part_number_match = re.match(part_number_pattern, remaining)
        
        if part_number_match:
            result["part_number"] = part_number_match.group(1)
            remaining = part_number_match.group(2).strip()
        else:
            # Try numeric prefix pattern: "24. Ротор сборка"
            # Pattern: ^(\d{1,3})\.\s*(.+)
            numeric_prefix_pattern = r'^(\d{1,3})\.\s*(.*)$'
            numeric_match = re.match(numeric_prefix_pattern, remaining)
            
            if numeric_match:
                result["part_number"] = numeric_match.group(1)
                remaining = numeric_match.group(2).strip()
        
        # Extract name: use remaining text or fallback to filename without extension
        if remaining:
            result["name"] = remaining.strip()
        else:
            result["name"] = name_without_ext.strip()
        
        # Final fallback: ensure name is never empty
        if not result["name"]:
            result["name"] = filename
            
    except Exception:
        # Parsing never blocks import: if regex fails, continue with fallback values
        result["section_code"] = None
        result["part_number"] = None
        result["name"] = filename if filename else "unnamed"
    
    return result

