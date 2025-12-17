"""
API Modules for Smart Tourist Safety System
"""

# Original modules (SQLAlchemy-based)
# These are kept for reference but should not be used in production

# Supabase-based modules (use these for production)
from app.api import tourists_supabase
from app.api import locations_supabase
from app.api import alerts_supabase
from app.api import efir_supabase
from app.api import zones_supabase
from app.api import safety_supabase

# Other modules that might not have been migrated yet
from app.api import frontend
from app.api import realtime
