"""
VBA Code Validator
Validates VBA syntax and structure
"""

from loguru import logger
from typing import Dict, List, Any
import re
from api.models import ValidationError


class VBAValidator:
    """Validates VBA code syntax and structure"""

    def __init__(self):
        # Common VBA keywords
        self.vba_keywords = {
            'Sub', 'Function', 'End', 'If', 'Then', 'Else', 'ElseIf',
            'For', 'Next', 'While', 'Wend', 'Do', 'Loop', 'Select', 'Case',
            'Dim', 'As', 'Set', 'Let', 'Const', 'Private', 'Public',
            'Exit', 'Return', 'Call', 'On', 'Error', 'GoTo', 'Resume'
        }

        # Common SOLIDWORKS API patterns
        self.solidworks_api_patterns = [
            r'swApp\.',
            r'swModel\.',
            r'swDoc\.',
            r'swModelDoc2\.',
            r'swSketch\.',
            r'swFeature\.',
            r'swPart\.',
            r'swAssembly\.',
            r'swDrawing\.',
            r'swSelectionMgr\.',
            r'swMathUtility\.'
        ]

    async def validate_syntax(
        self,
        code: str,
        strict: bool = True
    ) -> Dict[str, Any]:
        """
        Validate VBA code syntax

        Args:
            code: VBA code to validate
            strict: Enable strict validation

        Returns:
            Validation results with errors and warnings
        """
        errors = []
        warnings = []

        try:
            lines = code.split('\n')

            # Track Sub/Function blocks
            block_stack = []
            line_number = 0

            for line in lines:
                line_number += 1
                stripped = line.strip()

                if not stripped or stripped.startswith("'"):
                    continue  # Skip empty lines and comments

                # Check for Sub/Function declarations
                if re.match(r'^\s*(Public|Private)?\s*(Sub|Function)\s+\w+', stripped):
                    block_type = 'Function' if 'Function' in stripped else 'Sub'
                    block_stack.append(block_type)

                # Check for End Sub/Function
                if re.match(r'^\s*End\s+(Sub|Function)', stripped):
                    if not block_stack:
                        errors.append(ValidationError(
                            line_number=line_number,
                            error_type="syntax_error",
                            message=f"Unexpected 'End {stripped.split()[1]}' without matching declaration",
                            severity="error"
                        ))
                    else:
                        block_stack.pop()

                # Check for unmatched If/End If
                if re.match(r'^\s*If\s+.+\s+Then\s*$', stripped):
                    if 'End If' not in code[code.find(stripped):]:
                        warnings.append(ValidationError(
                            line_number=line_number,
                            error_type="control_flow",
                            message="If statement may be missing 'End If'",
                            severity="warning"
                        ))

                # Check for undeclared variables (simplified)
                if strict:
                    # Check for assignments without Dim
                    assignment_match = re.match(r'^\s*(\w+)\s*=', stripped)
                    if assignment_match and not re.match(r'^\s*Dim\s+', stripped):
                        var_name = assignment_match.group(1)
                        if var_name not in self.vba_keywords:
                            warnings.append(ValidationError(
                                line_number=line_number,
                                error_type="undeclared_variable",
                                message=f"Variable '{var_name}' may not be declared",
                                severity="warning"
                            ))

            # Check for unclosed blocks
            if block_stack:
                errors.append(ValidationError(
                    line_number=None,
                    error_type="syntax_error",
                    message=f"Unclosed {block_stack[-1]} block",
                    severity="error"
                ))

            syntax_valid = len(errors) == 0

            return {
                "syntax_valid": syntax_valid,
                "errors": [e.dict() for e in errors],
                "warnings": [w.dict() for w in warnings]
            }

        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            return {
                "syntax_valid": False,
                "errors": [ValidationError(
                    line_number=None,
                    error_type="validation_error",
                    message=str(e),
                    severity="error"
                ).dict()],
                "warnings": []
            }

    def extract_api_calls(self, code: str) -> List[str]:
        """
        Extract SOLIDWORKS API calls from VBA code

        Args:
            code: VBA code

        Returns:
            List of API calls found
        """
        api_calls = []

        for pattern in self.solidworks_api_patterns:
            matches = re.finditer(pattern + r'(\w+)', code)
            for match in matches:
                api_call = match.group(0)
                if api_call not in api_calls:
                    api_calls.append(api_call)

        return api_calls

    def check_best_practices(self, code: str) -> List[ValidationError]:
        """
        Check VBA code against best practices

        Returns:
            List of best practice violations
        """
        recommendations = []

        # Check for Option Explicit
        if 'Option Explicit' not in code:
            recommendations.append(ValidationError(
                line_number=1,
                error_type="best_practice",
                message="Consider adding 'Option Explicit' at the top of the module",
                severity="info"
            ))

        # Check for error handling
        if 'On Error' not in code:
            recommendations.append(ValidationError(
                line_number=None,
                error_type="best_practice",
                message="Consider adding error handling (On Error GoTo/Resume)",
                severity="info"
            ))

        # Check for comments
        comment_lines = len([l for l in code.split('\n') if l.strip().startswith("'")])
        total_lines = len([l for l in code.split('\n') if l.strip()])

        if total_lines > 10 and comment_lines == 0:
            recommendations.append(ValidationError(
                line_number=None,
                error_type="best_practice",
                message="Consider adding comments to explain the code",
                severity="info"
            ))

        return recommendations
