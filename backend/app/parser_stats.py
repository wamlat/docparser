import os
import json
from threading import Lock

# Use a lock to ensure thread-safety for counter updates
_stats_lock = Lock()

# Initialize counters for different parser methods
_ner_used = 0
_llm_fallback_used = 0  # when NER confidence is low
_llm_forced = 0  # when USE_LLM_PARSER=true

def increment_ner_counter():
    """Increment the counter for NER parser usage"""
    global _ner_used
    with _stats_lock:
        _ner_used += 1

def increment_llm_fallback_counter():
    """Increment the counter for LLM fallback parser usage"""
    global _llm_fallback_used
    with _stats_lock:
        _llm_fallback_used += 1

def increment_llm_forced_counter():
    """Increment the counter for forced LLM parser usage"""
    global _llm_forced
    with _stats_lock:
        _llm_forced += 1

def get_usage_stats():
    """
    Get current parser usage statistics
    
    Returns:
        dict: Dictionary containing usage counts for each parser type
    """
    with _stats_lock:
        return {
            "ner_used": _ner_used,
            "llm_fallback_used": _llm_fallback_used,
            "llm_forced": _llm_forced,
            "total_documents_processed": _ner_used + _llm_fallback_used + _llm_forced
        }

def reset_stats():
    """Reset all statistics counters to zero"""
    global _ner_used, _llm_fallback_used, _llm_forced
    with _stats_lock:
        _ner_used = 0
        _llm_fallback_used = 0
        _llm_forced = 0

def save_stats_to_file(filepath="parser_stats.json"):
    """
    Save current statistics to a JSON file
    
    Args:
        filepath (str): Path to save the statistics file
    """
    try:
        stats = get_usage_stats()
        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving stats to file: {str(e)}")
        return False

def load_stats_from_file(filepath="parser_stats.json"):
    """
    Load statistics from a JSON file
    
    Args:
        filepath (str): Path to the statistics file
        
    Returns:
        bool: True if loading was successful, False otherwise
    """
    global _ner_used, _llm_fallback_used, _llm_forced
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                stats = json.load(f)
                with _stats_lock:
                    _ner_used = stats.get("ner_used", 0)
                    _llm_fallback_used = stats.get("llm_fallback_used", 0)
                    _llm_forced = stats.get("llm_forced", 0)
            return True
        return False
    except Exception as e:
        print(f"Error loading stats from file: {str(e)}")
        return False 