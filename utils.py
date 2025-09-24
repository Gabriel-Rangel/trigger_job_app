"""
Utility functions shared across the application
"""

def get_string_value(obj):
    """
    Helper function to extract string from enum or object
    """
    if obj is None:
        return ""
    # If it's an enum, get the value
    if hasattr(obj, 'value'):
        return str(obj.value)
    # If it has a name attribute (enum name)
    elif hasattr(obj, 'name'):
        return str(obj.name)
    # Otherwise convert to string
    else:
        return str(obj)

def job_label(job):
    """
    Format job display label with name and ID
    """
    job_id = getattr(job, "job_id", None)
    name = getattr(job.settings, "name", None) if hasattr(job, "settings") else getattr(job, "name", None)
    return f"{name} (ID {job_id})" if name and job_id else str(job_id or "unknown")
