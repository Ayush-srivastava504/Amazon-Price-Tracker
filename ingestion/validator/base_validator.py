"""Abstract base classes for validators."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import structlog

logger = structlog.get_logger()

class BaseValidator(ABC):
    """Abstract base class for all validators."""
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate data.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data."""
        pass

class ValidationContext:
    """Context for validation chain."""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def add_error(self, error: str):
        """Add validation error."""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Add validation warning."""
        self.warnings.append(warning)
    
    def is_valid(self) -> bool:
        """Check if context has no errors."""
        return len(self.errors) == 0

class ValidatorChain:
    """Chain of responsibility pattern for validators."""
    
    def __init__(self):
        self.validators: List[BaseValidator] = []
    
    def add_validator(self, validator: BaseValidator):
        """Add validator to chain."""
        self.validators.append(validator)
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Run all validators in chain."""
        context = ValidationContext(data)
        
        for validator in self.validators:
            is_valid, error = validator.validate(data)
            if not is_valid and error:
                context.add_error(error)
        
        return context.is_valid(), context.errors