"""
SOLIDWORKS API Validator
Validates API calls against SOLIDWORKS API reference
"""

from loguru import logger
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from config.settings import settings


class APIValidator:
    """Validates SOLIDWORKS API calls"""

    def __init__(self):
        self.api_reference_path = Path(settings.API_REFERENCES_PATH)
        self.api_reference = {}
        self._load_api_reference()

    def _load_api_reference(self):
        """Load SOLIDWORKS API reference data"""
        try:
            # Load API reference files
            reference_files = list(self.api_reference_path.glob("*.json"))

            if not reference_files:
                logger.warning("No API reference files found, creating default reference")
                self._create_default_reference()
            else:
                for ref_file in reference_files:
                    with open(ref_file, 'r') as f:
                        data = json.load(f)
                        self.api_reference.update(data)

            logger.info(f"Loaded {len(self.api_reference)} API references")

        except Exception as e:
            logger.error(f"Failed to load API reference: {e}")
            self._create_default_reference()

    def _create_default_reference(self):
        """Create default SOLIDWORKS API reference"""
        # Common SOLIDWORKS API calls
        self.api_reference = {
            "swApp.CreateNewDocument": {
                "description": "Creates a new document",
                "parameters": ["template_path"],
                "return_type": "ModelDoc2"
            },
            "swApp.OpenDoc6": {
                "description": "Opens an existing document",
                "parameters": ["filename", "type", "options", "configuration", "errors", "warnings"],
                "return_type": "ModelDoc2"
            },
            "swModel.InsertSketch2": {
                "description": "Inserts a sketch",
                "parameters": ["edit_mode"],
                "return_type": "Boolean"
            },
            "swModel.CreateLine2": {
                "description": "Creates a line in a sketch",
                "parameters": ["x1", "y1", "z1", "x2", "y2", "z2"],
                "return_type": "SketchSegment"
            },
            "swModel.CreateCircle2": {
                "description": "Creates a circle in a sketch",
                "parameters": ["x", "y", "z", "radius"],
                "return_type": "SketchSegment"
            },
            "swModel.FeatureExtrusion3": {
                "description": "Creates an extrusion feature",
                "parameters": ["reverse", "flip", "dir", "type", "depth", "merge", "end_cap"],
                "return_type": "Feature"
            },
            "swModel.SaveAs3": {
                "description": "Saves the document",
                "parameters": ["filename", "save_as_version", "save_as_options"],
                "return_type": "Boolean"
            },
            "swModel.SelectionManager": {
                "description": "Gets the selection manager",
                "parameters": [],
                "return_type": "SelectionMgr"
            },
            "swSketch.InsertSketch": {
                "description": "Inserts a sketch",
                "parameters": [],
                "return_type": "Boolean"
            },
            "swFeature.GetTypeName2": {
                "description": "Gets feature type name",
                "parameters": [],
                "return_type": "String"
            }
        }

        # Save default reference
        self._save_api_reference()

    def _save_api_reference(self):
        """Save API reference to file"""
        try:
            self.api_reference_path.mkdir(parents=True, exist_ok=True)
            ref_file = self.api_reference_path / "solidworks_api_reference.json"

            with open(ref_file, 'w') as f:
                json.dump(self.api_reference, f, indent=2)

            logger.info("API reference saved")

        except Exception as e:
            logger.error(f"Failed to save API reference: {e}")

    async def validate_api_calls(self, code: str) -> List[str]:
        """
        Validate API calls in VBA code

        Args:
            code: VBA code to validate

        Returns:
            List of valid API calls found
        """
        import re

        valid_api_calls = []

        # Extract potential API calls
        # Pattern: object.Method or object.Property
        api_pattern = r'(sw\w+)\.\w+'
        matches = re.finditer(api_pattern, code)

        for match in matches:
            api_call = match.group(0)

            # Check if it's in our reference
            is_valid = any(api_call in ref_key for ref_key in self.api_reference.keys())

            if is_valid or self._is_likely_valid_api(api_call):
                if api_call not in valid_api_calls:
                    valid_api_calls.append(api_call)

        return valid_api_calls

    def _is_likely_valid_api(self, api_call: str) -> bool:
        """
        Check if an API call looks like a valid SOLIDWORKS API call

        Args:
            api_call: API call string

        Returns:
            True if it looks valid
        """
        # Check if it starts with common SOLIDWORKS prefixes
        valid_prefixes = ['swApp.', 'swModel.', 'swDoc.', 'swSketch.', 'swFeature.', 'swPart.']
        return any(api_call.startswith(prefix) for prefix in valid_prefixes)

    async def validate_single_call(self, api_call: str) -> Dict[str, Any]:
        """
        Validate a single API call

        Args:
            api_call: API call to validate

        Returns:
            Validation result with documentation
        """
        # Check exact match
        if api_call in self.api_reference:
            ref = self.api_reference[api_call]
            return {
                "is_valid": True,
                "documentation": ref.get("description"),
                "parameters": ref.get("parameters", []),
                "return_type": ref.get("return_type")
            }

        # Check partial match
        for ref_key in self.api_reference.keys():
            if api_call in ref_key or ref_key in api_call:
                ref = self.api_reference[ref_key]
                return {
                    "is_valid": True,
                    "documentation": ref.get("description"),
                    "parameters": ref.get("parameters", []),
                    "return_type": ref.get("return_type"),
                    "note": "Partial match"
                }

        # Check if it looks valid
        if self._is_likely_valid_api(api_call):
            return {
                "is_valid": True,
                "documentation": "API call appears valid but not in reference",
                "parameters": [],
                "return_type": "Unknown",
                "note": "Not in reference database"
            }

        return {
            "is_valid": False,
            "documentation": None,
            "parameters": [],
            "return_type": None
        }

    async def get_api_reference(self) -> List[Dict[str, Any]]:
        """
        Get complete API reference

        Returns:
            List of API calls with documentation
        """
        reference_list = []

        for api_call, details in self.api_reference.items():
            reference_list.append({
                "api_call": api_call,
                "description": details.get("description"),
                "parameters": details.get("parameters", []),
                "return_type": details.get("return_type")
            })

        return reference_list

    def add_api_reference(
        self,
        api_call: str,
        description: str,
        parameters: List[str],
        return_type: str
    ) -> bool:
        """
        Add a new API reference

        Args:
            api_call: API call name
            description: Description
            parameters: List of parameters
            return_type: Return type

        Returns:
            Success status
        """
        try:
            self.api_reference[api_call] = {
                "description": description,
                "parameters": parameters,
                "return_type": return_type
            }

            self._save_api_reference()
            logger.info(f"Added API reference: {api_call}")
            return True

        except Exception as e:
            logger.error(f"Failed to add API reference: {e}")
            return False
