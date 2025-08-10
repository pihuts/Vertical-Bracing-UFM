### **Refactoring Plan: `PryingActionCalculator` Generalization**

This document outlines the proposed changes to make the `PryingActionCalculator` more versatile by allowing it to handle various structural shapes, not just plates.

#### **1. Proposed Changes**

##### **1.1. `__init__` Method Signature Change**

The `__init__` method signature will be updated to accept generic member types.

*   **Current Signature:**
    ```python
    def __init__(self, plate: Plate, gusset: Plate, connection: Connection):
    ```

*   **Proposed Signature:**
    ```python
    from typing import Any
    # ...
    def __init__(self, member_1: Any, member_2: Any, connection: Connection):
    ```
    This change replaces the specific `Plate` type hints with `Any`, allowing any object (like a `steelpy` member) to be passed in.

##### **1.2. New Helper Method for Property Extraction**

A new private helper method, `_get_prying_properties`, will be introduced. This method will be responsible for inspecting a given member and extracting the properties required for the prying calculation. This centralizes the type-checking logic.

```python
def _get_prying_properties(self, member: Any) -> dict:
    """
    Extracts properties needed for prying calculations from a generic member.
    This acts as an adapter for different member types (Plate, W, L).
    """
    member_type = getattr(member, 'Type', None)

    if member_type == 'Plate' or isinstance(member, Plate):
        return {
            't': getattr(member, 't', 0),
            'width': getattr(member, 'width', 0),
            'Fu': getattr(member, 'Fu', 0)
        }
    elif member_type == 'W':
        # Assumption: Prying action occurs on the flange.
        return {
            't': getattr(member, 'tf', 0),      # Flange thickness
            'width': getattr(member, 'bf', 0),  # Flange width
            'Fu': getattr(member, 'Fu', 0)
        }
    elif member_type == 'L':
        return {
            't': getattr(member, 't', 0),       # Leg thickness
            'width': getattr(member, 'd', 0),   # Leg length (used as width)
            'Fu': getattr(member, 'Fu', 0)
        }
    else:
        # Fallback for unknown types or simple objects
        # This maintains backward compatibility if a simple Plate object is passed
        if all(hasattr(member, attr) for attr in ['t', 'width', 'Fu']):
             return {
                't': member.t,
                'width': member.width,
                'Fu': member.Fu
            }
        raise TypeError(f"Unsupported member type for prying calculation: {type(member)}")
```

**Note on W-Sections:** The user suggested using web thickness (`tw`). However, prying action is a bending phenomenon in a plate-like element under tension. When a W-section flange is bolted, it's the flange that bends. Therefore, I have proposed using the **flange thickness (`tf`)** and **flange width (`bf`)** as they are the mechanically correct properties to use for this calculation. This is a critical assumption that should be validated.

##### **1.3. Refactored `__init__` Logic**

The `__init__` method will be updated to use the new helper method to populate its internal variables.

*   **Current Logic (Simplified):**
    ```python
    self.plate = plate
    self.gusset = gusset
    self.t = self.plate.t
    self.width = self.plate.width
    self.gusset_thickness = self.gusset.t
    # ... uses self.plate.Fu later
    ```

*   **Proposed Logic (Simplified):**
    ```python
    self.connection = connection
    self.config: BoltConfiguration = connection.configuration

    # Extract properties from the two members
    props_1 = self._get_prying_properties(member_1)
    props_2 = self._get_prying_properties(member_2)

    # Assign properties for the main plate being analyzed
    self.t = props_1['t']
    self.width = props_1['width']
    self.plate_Fu = props_1['Fu'] # Store Fu for later use

    # Assign thickness for the supporting member (gusset)
    self.gusset_thickness = props_2['t']

    # ... rest of the calculations remain the same ...
    # e.g., self.a = (self.width - self.g) / 2
    # e.g., self.b = (self.g - self.gusset_thickness) / 2
    ```

#### **2. Pros & Cons**

##### **Pros:**
*   ✅ **Flexibility & Reusability:** The calculator will no longer be restricted to `Plate`-to-`Plate` connections. It can be used for W-section flanges, angle legs, and other components without needing a new class.
*   ✅ **Maintainability:** The logic for handling different shapes is contained within a single helper method (`_get_prying_properties`), making it easy to update or add new shapes in the future.
*   ✅ **Consistency:** This change aligns the `PryingActionCalculator` with the design pattern used by other calculators in `calculations.py` which handle generic `endpoint` and `member` objects.

##### **Cons:**
*   ❌ **Increased Complexity:** The `__init__` method becomes more abstract, and the introduction of the `_get_prying_properties` method adds a layer of indirection.
*   ❌ **Engineering Assumptions:** The mapping from section properties (e.g., W-section `bf` to prying `width`) relies on engineering assumptions. While the proposed mappings are based on standard practice, they must be correct. The assumption of using flange properties for a W-section is a key example.
*   ❌ **Risk & Testing:** As with any refactoring, there is a risk of introducing bugs. A thorough testing strategy will be needed to verify that the new implementation works correctly for all member types and that the original `Plate` functionality is not broken.