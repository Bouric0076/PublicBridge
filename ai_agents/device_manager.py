import torch
import logging
import platform
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DeviceManager:
    """
    Centralized device management for AI models.
    Handles device initialization, memory management, and fallback strategies.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeviceManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.device = None
            self.device_type = None
            self.memory_info = {}
            self.system_info = {}
            self._initialize_device()
            DeviceManager._initialized = True
    
    def _initialize_device(self):
        """Initialize the optimal device for AI operations."""
        try:
            logger.info("Initializing device manager...")
            
            # Collect system information
            self.system_info = {
                'platform': platform.system(),
                'architecture': platform.architecture()[0],
                'python_version': platform.python_version(),
                'torch_version': torch.__version__
            }
            
            # Check for CUDA availability
            if torch.cuda.is_available():
                self.device = torch.device('cuda')
                self.device_type = 'cuda'
                
                # Get GPU memory info
                gpu_count = torch.cuda.device_count()
                current_device = torch.cuda.current_device()
                gpu_name = torch.cuda.get_device_name(current_device)
                
                self.memory_info = {
                    'gpu_count': gpu_count,
                    'current_device': current_device,
                    'gpu_name': gpu_name,
                    'total_memory': torch.cuda.get_device_properties(current_device).total_memory,
                    'allocated_memory': torch.cuda.memory_allocated(current_device),
                    'cached_memory': torch.cuda.memory_reserved(current_device)
                }
                
                logger.info(f"CUDA device initialized: {gpu_name}")
                
            # Check for MPS (Apple Silicon) availability
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = torch.device('mps')
                self.device_type = 'mps'
                self.memory_info = {'device_type': 'mps', 'unified_memory': True}
                logger.info("MPS device initialized (Apple Silicon)")
                
            # Fallback to CPU
            else:
                self.device = torch.device('cpu')
                self.device_type = 'cpu'
                self.memory_info = {'device_type': 'cpu', 'cores': torch.get_num_threads()}
                logger.info("CPU device initialized")
            
            # Log device information
            logger.info(f"Device manager initialized - Type: {self.device_type}, Device: {self.device}")
            
        except Exception as e:
            logger.error(f"Device initialization failed: {e}")
            # Fallback to CPU
            self.device = torch.device('cpu')
            self.device_type = 'cpu'
            self.memory_info = {'device_type': 'cpu', 'error': str(e)}
    
    def get_device(self) -> torch.device:
        """Get the initialized device."""
        return self.device
    
    def get_device_type(self) -> str:
        """Get the device type string."""
        return self.device_type
    
    def is_gpu_available(self) -> bool:
        """Check if GPU is available and being used."""
        return self.device_type in ['cuda', 'mps']
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get current memory information."""
        if self.device_type == 'cuda':
            current_device = torch.cuda.current_device()
            self.memory_info.update({
                'allocated_memory': torch.cuda.memory_allocated(current_device),
                'cached_memory': torch.cuda.memory_reserved(current_device),
                'free_memory': self.memory_info['total_memory'] - torch.cuda.memory_allocated(current_device)
            })
        
        return self.memory_info.copy()
    
    def clear_cache(self):
        """Clear GPU cache if available."""
        try:
            if self.device_type == 'cuda':
                torch.cuda.empty_cache()
                logger.info("CUDA cache cleared")
            elif self.device_type == 'mps':
                torch.mps.empty_cache()
                logger.info("MPS cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
    
    def get_optimal_dtype(self) -> torch.dtype:
        """Get optimal data type for the current device."""
        if self.is_gpu_available():
            return torch.float16  # Use half precision for GPU
        else:
            return torch.float32  # Use full precision for CPU
    
    def get_device_map(self) -> str:
        """Get optimal device map configuration."""
        if self.is_gpu_available():
            return "auto"
        else:
            return None
    
    def should_use_quantization(self) -> bool:
        """Determine if quantization should be used based on device and memory."""
        if not self.is_gpu_available():
            return False
        
        if self.device_type == 'cuda':
            # Use quantization if GPU memory is limited
            memory_info = self.get_memory_info()
            total_memory_gb = memory_info.get('total_memory', 0) / (1024**3)
            return total_memory_gb < 12  # Use quantization for GPUs with less than 12GB
        
        return False
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get recommended model configuration for current device."""
        config = {
            'device_map': self.get_device_map(),
            'dtype': self.get_optimal_dtype(),
            'low_cpu_mem_usage': True
        }
        
        # Add quantization config if recommended
        if self.should_use_quantization():
            try:
                from transformers import BitsAndBytesConfig
                config['quantization_config'] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            except ImportError:
                logger.warning("BitsAndBytesConfig not available, skipping quantization")
        
        return config
    
    def is_windows_development(self) -> bool:
        """Check if running on Windows (typically development environment)."""
        return self.system_info.get('platform', '').lower().startswith('win')
    
    def should_skip_heavy_models(self) -> bool:
        """Determine if heavy models should be skipped."""
        # Skip heavy models on Windows or low-memory systems
        if self.is_windows_development():
            return True
        
        if self.device_type == 'cpu':
            return True
        
        if self.device_type == 'cuda':
            memory_info = self.get_memory_info()
            total_memory_gb = memory_info.get('total_memory', 0) / (1024**3)
            return total_memory_gb < 6  # Skip if less than 6GB GPU memory
        
        return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        info = self.system_info.copy()
        info.update({
            'device': str(self.device),
            'device_type': self.device_type,
            'memory_info': self.get_memory_info(),
            'skip_heavy_models': self.should_skip_heavy_models(),
            'use_quantization': self.should_use_quantization()
        })
        return info
    
    def health_check(self) -> Dict[str, Any]:
        """Perform device health check."""
        try:
            # Test basic tensor operations
            test_tensor = torch.randn(10, 10).to(self.device)
            result = torch.matmul(test_tensor, test_tensor.T)
            
            return {
                'status': 'healthy',
                'device': str(self.device),
                'device_type': self.device_type,
                'tensor_operations': 'working',
                'memory_info': self.get_memory_info(),
                'system_info': self.system_info
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'device': str(self.device) if self.device else 'unknown',
                'device_type': self.device_type
            }

# Global device manager instance
device_manager = DeviceManager()

# Convenience functions
def get_device() -> torch.device:
    """Get the global device."""
    return device_manager.get_device()

def get_device_type() -> str:
    """Get the global device type."""
    return device_manager.get_device_type()

def get_model_config() -> Dict[str, Any]:
    """Get recommended model configuration."""
    return device_manager.get_model_config()

def should_skip_heavy_models() -> bool:
    """Check if heavy models should be skipped."""
    return device_manager.should_skip_heavy_models()

def clear_cache():
    """Clear device cache."""
    device_manager.clear_cache()

def health_check() -> Dict[str, Any]:
    """Perform device health check."""
    return device_manager.health_check()
