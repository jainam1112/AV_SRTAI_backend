# Utility functions for error handling, progress tracking, etc.

def error_response(message: str):
    return {"success": False, "error": message}

def success_response(data):
    return {"success": True, "data": data}
