import logging
import traceback

__all__ = []

try:
    from .generate_lean_impl import c_type_name
    from .generate_lean_impl import escape_lean_ident
    from .generate_lean_impl import generate_lean
    from .generate_lean_impl import lean_accessor_type
    from .generate_lean_impl import lean_field_type
    from .generate_lean_impl import lean_type_name
    from .generate_lean_impl import package_module_name
    __all__ += [
        'c_type_name', 'escape_lean_ident', 'generate_lean',
        'lean_accessor_type', 'lean_field_type', 'lean_type_name',
        'package_module_name',
    ]
except ImportError:
    logger = logging.getLogger('rosidl_generator_lean')
    logger.debug(
        'Failed to import modules for generating Lean structures:\n' +
        traceback.format_exc())
