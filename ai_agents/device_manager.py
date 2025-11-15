import logging
import platform
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DeviceManager:
    """
    Lightweight device management for AI models.
    Simplified version without torch dependencies for Render deployment.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeviceManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.device = 'cpu'
            self.device_type = 'cpu'
            self.memory_info = {}
            self.system_info = {}
            self._initialize_device()
            DeviceManager._initialized = True
    
    def _initialize_device(self):
        """Initialize the device information (CPU only for lightweight deployment)."""
        try:
            logger.info("Initializing lightweight device manager...")
            
            # Collect basic system information
            self.system_info = {
                'platform': platform.system(),
                'architecture': platform.architecture()[0],
                'python_version': platform.python_version(),
                'device_type': 'cpu',
                'deployment_type': 'lightweight'
            }
            
            # Set CPU as default device (no GPU/CUDA dependencies)
            self.device = 'cpu'
            self.device_type = 'cpu'
            self.memory_info = {
                'device_type': 'cpu',
                'note': 'Lightweight deployment - no GPU acceleration'
            }
            
            logger.info("Device manager initialized for CPU-only deployment")
            
        except Exception as e:
            logger.error(f"Device initialization failed: {e}")
            # Fallback to basic CPU
            self.device = 'cpu'
            self.device_type = 'cpu'
            self.memory_info = {'device_type': 'cpu', 'error': str(e)}
    
    def get_device(self) -> str:
        """Get the initialized device."""
        return self.device
    
    def get_device_type(self) -> str:
        """Get the device type string."""
        return self.device_type
    
    def is_gpu_available(self) -> bool:
        """Check if GPU is available and being used."""
        return False  # Always return False for lightweight deployment
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information."""
        return self.memory_info
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return self.system_info
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration based on device capabilities."""
        return {
            'device': self.device,
            'device_type': self.device_type,
            'max_batch_size': 1,  # Conservative for lightweight deployment
            'precision': 'fp32',  # Standard precision
            'optimization_level': 'basic'
        }
    
    def should_skip_heavy_models(self) -> bool:
        """Determine if heavy models should be skipped."""
        return True  # Always skip heavy models in lightweight deployment
    
    def clear_cache(self):
        """Clear any device caches."""
        logger.info("Cache cleared (no-op for lightweight deployment)")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform device health check."""
        try:
            # Simple health check without tensor operations
            return {
                'status': 'healthy',
                'device': self.device,
                'device_type': self.device_type,
                'deployment_type': 'lightweight',
                'memory_info': self.memory_info,
                'system_info': self.system_info
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'device': self.device,
                'device_type': self.device_type
            }

# Global device manager instance
device_manager = DeviceManager()

# Convenience functions
def get_device() -> str:
    """Get the global device."""
    return device_manager.get_device()

def get_device_type() -> str:
    """Get the global device type."""
    return device_manager.get_device_type()

def is_gpu_available() -> bool:
    """Check if GPU is available globally."""
    return device_manager.is_gpu_available()

def get_memory_info() -> Dict[str, Any]:
    """Get global memory information."""
    return device_manager.get_memory_info()

def get_model_config() -> Dict[str, Any]:
    """Get model configuration."""
    return device_manager.get_model_config()

def should_skip_heavy_models() -> bool:
    """Check if heavy models should be skipped."""
    return device_manager.should_skip_heavy_models()

def clear_cache():
    """Clear global cache."""
    device_manager.clear_cache()

def health_check() -> Dict[str, Any]:
    """Perform global health check."""
    return device_manager.health_check()
