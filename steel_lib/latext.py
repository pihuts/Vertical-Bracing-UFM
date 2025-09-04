from pydantic import BaseModel, Field
from typing import Dict

class LatexConfig(BaseModel):
    """A Pydantic model for managing LaTeX configuration."""
    
    main_title: str
    
    # The 'Field' is now imported from Pydantic, but the usage is the same.
    sub_title: Dict[str, str] = Field(default_factory=dict)

    # --- Your custom methods are copied directly, with no changes needed ---
    def add_subtitle(self, key: str, value: str):
        """Adds or updates a subtitle in the dictionary."""
        self.sub_title[key] = value

    def remove_subtitle(self, key: str):
        """Removes a subtitle from the dictionary if it exists."""
        if key in self.sub_title:
            del self.sub_title[key]