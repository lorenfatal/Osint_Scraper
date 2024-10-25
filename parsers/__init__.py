# This file handles the dynamic importing of parser modules and maintains the parser_registry

import pkgutil      # find and load modules
import importlib    # import modules dynamically

parser_registry = []

# Registers a parser instance in the parser_registry
def register_parser(parser_instance):
    parser_registry.append(parser_instance)

# Dynamically import all parser modules in the current package
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    if module_name.endswith('_parser'):
        importlib.import_module(f'{__name__}.{module_name}')
