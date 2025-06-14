from .audio_routes import bp as audio_bp
from .feihualing_routes import bp as feihualing_bp
from .ninegrid_routes import bp as ninegrid_bp
from .recitation_routes import bp as recitation_bp
from .deepseek import bp as chat_bp

__all__ = ['audio_bp', 'feihualing_bp', 'ninegrid_bp', 'recitation_bp','chat_bp']