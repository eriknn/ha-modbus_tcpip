import asyncio
import logging
import os

from importlib import import_module

_LOGGER = logging.getLogger(__name__)

async def get_available_drivers():
    # Get the base path to the "devices" folder
    base_path = os.path.dirname(os.path.abspath(__file__))  # Path to "devices/helpers.py"

    # Offload the blocking os.walk() operation to a separate thread
    return await asyncio.to_thread(scan_drivers, base_path)

def scan_drivers(base_path):
    drivers = []
    for root, _, files in os.walk(base_path):
        if root == base_path:  # Skip files in the "devices/" root directory
            continue
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                # Create the module path relative to the "devices/" folder
                relative_path = os.path.relpath(os.path.join(root, file), base_path)
                driver_path = relative_path.replace(os.sep, ".").rstrip(".py")
                drivers.append(driver_path)
    return drivers

async def load_device_class(driver_name):
    # Define the base package path
    base_package = "custom_components.modbus_tcpip"  # Your custom integration package path
    
    # Create the module path (e.g., "devices.Trox.TVE")
    module_path = f".devices.{driver_name}"

    try:
        # Dynamically import the module
        #driver_module = importlib.import_module(module_path, package=base_package)
        driver_module = await asyncio.to_thread(import_module, module_path, base_package)

        # Load tye class named 'Device' in the module
        device_class = getattr(driver_module, 'Device')
        
        return device_class
        
    except AttributeError as e:
        # If the 'Device' class is not found in the module, print the error
        _LOGGER.debug(f"AttributeError: {e} - Class 'Device' not found in {module_path}")
        return None
    except ModuleNotFoundError as e:
        # Handle the case where the module itself can't be found
        _LOGGER.debug(f"ModuleNotFoundError: {e} - Module {module_path} not found.")
        return None
    except Exception as e:
        # Handle any other exceptions that may arise
        _LOGGER.debug(f"Error: {e} while loading module {module_path}")
        return None