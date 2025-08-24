from typing import Any, Dict, Union
from .si_units import si
from .data_models import DesignLoads

class DebugLogger:
    """
    A helper class to standardize the format of debugging output for calculations.
    It collects inputs, intermediate calculations, and final outputs, and then
    displays them in a consistent, formatted table.
    """
    def __init__(self, title: str, debug: bool = False):
        """
        Initializes the logger.

        Args:
            title (str): The title for the debug output block.
            debug (bool): A flag to enable or disable logging. If False, all
                          methods will do nothing.
        """
        self.debug = debug
        self.title = title
        self.inputs: Dict[str, Any] = {}
        self.calculations: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}

    def add_input(self, name: str, value: Any):
        """Adds a value to the 'Inputs' section."""
        if self.debug:
            self.inputs[name] = value

    def add_calculation(self, name: str, value: Any):
        """Adds a value to the 'Calculations' section."""
        if self.debug:
            self.calculations[name] = value

    def add_output(self, name: str, value: Any):
        """Adds a value to the 'Output' section."""
        if self.debug:
            self.outputs[name] = value

    def _format_value(self, value: Any) -> str:
        """
        Formats a value for display, converting force units to 'kip' for
        consistency.
        """
        # Check if the value is a DesignLoads object
        if isinstance(value, DesignLoads):
            pu_str = self._format_value(value.Pu)
            vu_str = self._format_value(value.Vu)
            return f"DesignLoads(Pu={pu_str}, Vu={vu_str})"
        
        if hasattr(value, 'units'):
            try:
                # Try to convert to kip; if it works, it's a force.
                return f"{value.to('kip'):.4f} kip"
            except Exception:  # Catches conversion errors if not a force
                try:
                    # If not a force, format as a standard number
                    return f"{value:.4f} {value.units}"
                except (TypeError, ValueError):
                    # Fallback for non-numeric unit objects
                    return str(value)
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    def display(self):
        """Prints the collected debug information to the console."""
        if not self.debug:
            return

        print(f"\n--- DEBUG: {self.title} ---")

        if self.inputs:
            print("  Inputs:")
            for name, value in self.inputs.items():
                print(f"    {name:<35}: {self._format_value(value)}")

        if self.calculations:
            print("  Calculations:")
            for name, value in self.calculations.items():
                print(f"    {name:<35}: {self._format_value(value)}")

        if self.outputs:
            print("  Output:")
            print(f"    {'':<35}  --------------------")
            for name, value in self.outputs.items():
                print(f"    {name:<35}: {self._format_value(value)}")
        
        print(f"--- END DEBUG: {self.title} ---\
")
