"""
Validation Workflow Comprehensive Logging - Phase 6
==================================================

Comprehensive logging system for all validation workflows in circuit generation,
including code validation, circuit validation, netlist validation, and KiCad validation.
"""

import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .generation_logger import GenerationStage, generation_logger
from .unified_logger import context_logger, performance_logger


class ValidationType(Enum):
    """Types of validation performed in the circuit generation pipeline."""

    SYNTAX_VALIDATION = "syntax_validation"
    SEMANTIC_VALIDATION = "semantic_validation"
    CIRCUIT_VALIDATION = "circuit_validation"
    COMPONENT_VALIDATION = "component_validation"
    CONNECTION_VALIDATION = "connection_validation"
    NETLIST_VALIDATION = "netlist_validation"
    KICAD_VALIDATION = "kicad_validation"
    PCB_VALIDATION = "pcb_validation"
    DESIGN_RULE_VALIDATION = "design_rule_validation"
    ELECTRICAL_VALIDATION = "electrical_validation"


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Individual validation issue."""

    severity: ValidationSeverity
    message: str
    code: Optional[str]
    line_number: Optional[int]
    column_number: Optional[int]
    component: Optional[str]
    suggestion: Optional[str]
    context: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "severity": self.severity.value,
        }


@dataclass
class ValidationResult:
    """Comprehensive validation result."""

    validation_type: ValidationType
    stage: GenerationStage
    success: bool
    duration_ms: float
    issues: List[ValidationIssue]
    context: Dict[str, Any]
    timestamp: datetime
    validator_version: str

    @property
    def error_count(self) -> int:
        return len(
            [
                issue
                for issue in self.issues
                if issue.severity
                in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
            ]
        )

    @property
    def warning_count(self) -> int:
        return len(
            [
                issue
                for issue in self.issues
                if issue.severity == ValidationSeverity.WARNING
            ]
        )

    @property
    def info_count(self) -> int:
        return len(
            [
                issue
                for issue in self.issues
                if issue.severity == ValidationSeverity.INFO
            ]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_type": self.validation_type.value,
            "stage": self.stage.value,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "issues": [issue.to_dict() for issue in self.issues],
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "validator_version": self.validator_version,
            "statistics": {
                "total_issues": len(self.issues),
                "error_count": self.error_count,
                "warning_count": self.warning_count,
                "info_count": self.info_count,
                "success_rate": 1.0 if self.success else 0.0,
            },
        }


class ValidationLogger:
    """Comprehensive validation workflow logger."""

    def __init__(self):
        self.validation_history: List[ValidationResult] = []
        self._validation_stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "total_issues_found": 0,
            "total_validation_time_ms": 0.0,
            "validation_type_counts": {},
            "stage_validation_counts": {},
        }

    def validate_with_logging(
        self,
        validation_type: ValidationType,
        stage: GenerationStage,
        validator_func: callable,
        *args,
        **kwargs,
    ) -> ValidationResult:
        """
        Execute validation with comprehensive logging.

        Args:
            validation_type: Type of validation being performed
            stage: Generation stage where validation occurs
            validator_func: Function that performs the actual validation
            *args, **kwargs: Arguments passed to the validator function

        Returns:
            ValidationResult with comprehensive validation data
        """
        start_time = time.time()

        context_logger.info(
            f"Starting {validation_type.value} validation",
            component="VALIDATION_START",
            validation_type=validation_type.value,
            stage=stage.value,
        )

        try:
            # Execute the validation function
            validation_output = validator_func(*args, **kwargs)

            # Parse validation output
            issues = self._parse_validation_output(validation_output, validation_type)
            success = (
                len(
                    [
                        issue
                        for issue in issues
                        if issue.severity
                        in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
                    ]
                )
                == 0
            )

            duration_ms = (time.time() - start_time) * 1000

            # Create validation result
            result = ValidationResult(
                validation_type=validation_type,
                stage=stage,
                success=success,
                duration_ms=duration_ms,
                issues=issues,
                context=kwargs.get("context", {}),
                timestamp=datetime.now(),
                validator_version=self._get_validator_version(validation_type),
            )

            # Log the result
            self._log_validation_result(result)

            # Update statistics
            self._update_validation_stats(result)

            # Store in history
            self.validation_history.append(result)

            # Log to generation logger
            generation_logger.log_validation_result(
                stage=stage,
                validation_type=validation_type.value,
                success=success,
                errors=[
                    issue.message
                    for issue in issues
                    if issue.severity
                    in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
                ],
                warnings=[
                    issue.message
                    for issue in issues
                    if issue.severity == ValidationSeverity.WARNING
                ],
                duration_ms=duration_ms,
                context=result.context,
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Create error result
            error_issue = ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message=f"Validation failed with exception: {str(e)}",
                code="VALIDATION_EXCEPTION",
                line_number=None,
                column_number=None,
                component=None,
                suggestion="Check validation function implementation",
                context={
                    "exception_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                },
            )

            result = ValidationResult(
                validation_type=validation_type,
                stage=stage,
                success=False,
                duration_ms=duration_ms,
                issues=[error_issue],
                context={"error": str(e)},
                timestamp=datetime.now(),
                validator_version=self._get_validator_version(validation_type),
            )

            self._log_validation_error(result, e)
            self._update_validation_stats(result)
            self.validation_history.append(result)

            return result

    def validate_circuit_syntax(
        self, code: str, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate circuit code syntax."""

        def syntax_validator(code: str) -> Dict[str, Any]:
            issues = []

            # Basic syntax checks
            if not code.strip():
                issues.append(
                    {
                        "severity": "error",
                        "message": "Empty code provided",
                        "code": "EMPTY_CODE",
                    }
                )
                return {"issues": issues}

            # Check for basic Python syntax
            try:
                compile(code, "<string>", "exec")
            except SyntaxError as e:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"Python syntax error: {e.msg}",
                        "code": "PYTHON_SYNTAX_ERROR",
                        "line_number": e.lineno,
                        "column_number": e.offset,
                    }
                )

            # Check for Circuit Synth specific patterns
            if "circuit_synth" not in code.lower():
                issues.append(
                    {
                        "severity": "warning",
                        "message": "No Circuit Synth imports detected",
                        "code": "MISSING_CIRCUIT_SYNTH_IMPORT",
                        "suggestion": "Add: from circuit_synth import *",
                    }
                )

            return {"issues": issues}

        return self.validate_with_logging(
            ValidationType.SYNTAX_VALIDATION,
            GenerationStage.CODE_VALIDATION,
            syntax_validator,
            code,
            context=context or {},
        )

    def validate_circuit_semantics(
        self, circuit_obj, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate circuit semantic correctness."""

        def semantic_validator(circuit_obj) -> Dict[str, Any]:
            issues = []

            # Check for required components
            if not hasattr(circuit_obj, "components") or not circuit_obj.components:
                issues.append(
                    {
                        "severity": "error",
                        "message": "No components found in circuit",
                        "code": "NO_COMPONENTS",
                    }
                )

            # Check for connections
            if hasattr(circuit_obj, "nets"):
                if not circuit_obj.nets:
                    issues.append(
                        {
                            "severity": "warning",
                            "message": "No connections found in circuit",
                            "code": "NO_CONNECTIONS",
                            "suggestion": "Add connections between components",
                        }
                    )

            # Check for power connections
            has_power = False
            if hasattr(circuit_obj, "components"):
                for component in circuit_obj.components:
                    if hasattr(component, "reference") and any(
                        power_ref in component.reference.lower()
                        for power_ref in ["vcc", "vdd", "power", "supply"]
                    ):
                        has_power = True
                        break

            if not has_power:
                issues.append(
                    {
                        "severity": "warning",
                        "message": "No power supply components detected",
                        "code": "NO_POWER_SUPPLY",
                        "suggestion": "Consider adding power supply components",
                    }
                )

            return {"issues": issues}

        return self.validate_with_logging(
            ValidationType.SEMANTIC_VALIDATION,
            GenerationStage.CODE_VALIDATION,
            semantic_validator,
            circuit_obj,
            context=context or {},
        )

    def validate_netlist(
        self, netlist_path: str, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate generated netlist."""

        def netlist_validator(netlist_path: str) -> Dict[str, Any]:
            issues = []

            try:
                with open(netlist_path, "r") as f:
                    netlist_content = f.read()

                # Check file is not empty
                if not netlist_content.strip():
                    issues.append(
                        {
                            "severity": "error",
                            "message": "Netlist file is empty",
                            "code": "EMPTY_NETLIST",
                        }
                    )
                    return {"issues": issues}

                # Check for basic netlist structure
                if "(export" not in netlist_content:
                    issues.append(
                        {
                            "severity": "error",
                            "message": "Invalid netlist format - missing export section",
                            "code": "INVALID_NETLIST_FORMAT",
                        }
                    )

                # Check for components
                if (
                    "(comp" not in netlist_content
                    and "(component" not in netlist_content
                ):
                    issues.append(
                        {
                            "severity": "warning",
                            "message": "No components found in netlist",
                            "code": "NO_NETLIST_COMPONENTS",
                        }
                    )

                # Check for nets
                if "(net" not in netlist_content:
                    issues.append(
                        {
                            "severity": "warning",
                            "message": "No nets found in netlist",
                            "code": "NO_NETLIST_NETS",
                        }
                    )

            except FileNotFoundError:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"Netlist file not found: {netlist_path}",
                        "code": "NETLIST_FILE_NOT_FOUND",
                    }
                )
            except Exception as e:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"Error reading netlist: {str(e)}",
                        "code": "NETLIST_READ_ERROR",
                    }
                )

            return {"issues": issues}

        return self.validate_with_logging(
            ValidationType.NETLIST_VALIDATION,
            GenerationStage.NETLIST_GENERATION,
            netlist_validator,
            netlist_path,
            context=context or {},
        )

    def _parse_validation_output(
        self, output: Any, validation_type: ValidationType
    ) -> List[ValidationIssue]:
        """Parse validation output into standardized issues."""
        issues = []

        if isinstance(output, dict) and "issues" in output:
            for issue_data in output["issues"]:
                issue = ValidationIssue(
                    severity=ValidationSeverity(issue_data.get("severity", "error")),
                    message=issue_data.get("message", "Unknown validation issue"),
                    code=issue_data.get("code"),
                    line_number=issue_data.get("line_number"),
                    column_number=issue_data.get("column_number"),
                    component=issue_data.get("component"),
                    suggestion=issue_data.get("suggestion"),
                    context=issue_data.get("context", {}),
                )
                issues.append(issue)

        return issues

    def _log_validation_result(self, result: ValidationResult):
        """Log validation result with appropriate level."""
        result_data = result.to_dict()

        if result.success:
            if result.warning_count > 0:
                context_logger.warning(
                    f"Validation {result.validation_type.value} completed with warnings",
                    component="VALIDATION_WARNING",
                    validation_result=result_data,
                )
            else:
                context_logger.info(
                    f"Validation {result.validation_type.value} passed",
                    component="VALIDATION_SUCCESS",
                    validation_result=result_data,
                )
        else:
            context_logger.error(
                f"Validation {result.validation_type.value} failed",
                component="VALIDATION_FAILURE",
                validation_result=result_data,
            )

        # Log performance metrics
        performance_logger.log_metric(
            f"validation_{result.validation_type.value}_duration",
            result.duration_ms,
            unit="ms",
            component="VALIDATION_PERFORMANCE",
        )

    def _log_validation_error(self, result: ValidationResult, exception: Exception):
        """Log validation error with full context."""
        context_logger.error(
            f"Validation {result.validation_type.value} failed with exception",
            component="VALIDATION_EXCEPTION",
            validation_result=result.to_dict(),
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            traceback=traceback.format_exc(),
        )

    def _update_validation_stats(self, result: ValidationResult):
        """Update validation statistics."""
        self._validation_stats["total_validations"] += 1
        if result.success:
            self._validation_stats["successful_validations"] += 1

        self._validation_stats["total_issues_found"] += len(result.issues)
        self._validation_stats["total_validation_time_ms"] += result.duration_ms

        # Update type counts
        validation_type = result.validation_type.value
        if validation_type not in self._validation_stats["validation_type_counts"]:
            self._validation_stats["validation_type_counts"][validation_type] = 0
        self._validation_stats["validation_type_counts"][validation_type] += 1

        # Update stage counts
        stage = result.stage.value
        if stage not in self._validation_stats["stage_validation_counts"]:
            self._validation_stats["stage_validation_counts"][stage] = 0
        self._validation_stats["stage_validation_counts"][stage] += 1

    def _get_validator_version(self, validation_type: ValidationType) -> str:
        """Get version of the validator being used."""
        # This would return actual version information in practice
        return f"v1.0.0-{validation_type.value}"

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics."""
        stats = self._validation_stats.copy()

        if stats["total_validations"] > 0:
            stats["success_rate"] = (
                stats["successful_validations"] / stats["total_validations"] * 100
            )
            stats["avg_validation_time_ms"] = (
                stats["total_validation_time_ms"] / stats["total_validations"]
            )
            stats["avg_issues_per_validation"] = (
                stats["total_issues_found"] / stats["total_validations"]
            )

        return stats

    def get_recent_validation_summary(self, limit: int = 10) -> Dict[str, Any]:
        """Get summary of recent validations."""
        recent_validations = self.validation_history[-limit:]

        return {
            "total_recent": len(recent_validations),
            "successful": len([v for v in recent_validations if v.success]),
            "failed": len([v for v in recent_validations if not v.success]),
            "total_issues": sum(len(v.issues) for v in recent_validations),
            "avg_duration_ms": sum(v.duration_ms for v in recent_validations)
            / max(len(recent_validations), 1),
            "validation_types": list(
                set(v.validation_type.value for v in recent_validations)
            ),
            "stages": list(set(v.stage.value for v in recent_validations)),
        }


# Global instance
validation_logger = ValidationLogger()


# Convenience functions
def validate_circuit_syntax(
    code: str, context: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """Validate circuit code syntax."""
    return validation_logger.validate_circuit_syntax(code, context)


def validate_circuit_semantics(
    circuit_obj, context: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """Validate circuit semantic correctness."""
    return validation_logger.validate_circuit_semantics(circuit_obj, context)


def validate_netlist(
    netlist_path: str, context: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """Validate generated netlist."""
    return validation_logger.validate_netlist(netlist_path, context)
