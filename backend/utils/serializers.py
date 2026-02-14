"""
Serialization utilities
"""
from typing import Any, Dict, List, Set, Tuple

def sanitize_json_data(data: Any, seen: Set[int] = None) -> Any:
    """
    Sanitize data to prevent circular references in JSON serialization.
    
    Args:
        data: The data to sanitize
        seen: Set of object IDs that have been visited (for recursion detection)
        
    Returns:
        Sanitized data safe for JSON serialization
    """
    if seen is None:
        seen = set()
    
    # Primitives
    if isinstance(data, (str, int, float, bool, type(None))):
        return data
        
    # Check cycle
    obj_id = id(data)
    if obj_id in seen:
        return f"<Circular Reference {type(data).__name__}>"
    
    # Add to seen path
    new_seen = seen | {obj_id}
    
    if isinstance(data, dict):
        return {str(k): sanitize_json_data(v, new_seen) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_data(i, new_seen) for i in data]
    elif isinstance(data, tuple):
        return tuple(sanitize_json_data(i, new_seen) for i in data)
        
    # For other objects, return as is (let json.dumps default=str handle them)
    # Or convert to string representation if it's a known problematic type
    # But for now we rely on json.dumps default=str
    return data
