"""Mappers translating domain aggregates into application response DTOs.

Use cases must not return domain entities, because application contracts deal
in DTOs. These mappers centralize attribute conversion, including identifier
value objects mapped to their bare UUID values.
"""

from src.application.dto.collaborator_dtos import (
    CollaboratorResponseDTO,
    EnrollmentDTO,
)
from src.application.dto.competency_dtos import CompetencyResponseDTO
from src.application.dto.evaluation_dtos import (
    EvaluationResponseDTO,
    MeasurementDTO,
)
from src.application.dto.gap_analysis_dtos import (
    CompetencyGapDTO,
    ProgressionEligibilityDTO,
)
from src.application.dto.path_dtos import (
    LevelResponseDTO,
    PathResponseDTO,
    RequirementResponseDTO,
)
from src.domain.entities.collaborator import Collaborator
from src.domain.entities.competency import Competency
from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.entities.competency_path import CompetencyPath
from src.domain.entities.evaluation import Evaluation
from src.domain.entities.path_level import PathLevel
from src.domain.value_objects.competency_gap import CompetencyGap
from src.domain.value_objects.path_enrollment import PathEnrollment
from src.domain.value_objects.progression_eligibility import ProgressionEligibility


def map_competency(competency: Competency) -> CompetencyResponseDTO:
    """
    Map a competency entity to its response DTO.

    Args:
        competency: The stored competency.

    Returns:
        The response DTO with identifier values converted from value objects.
    """
    return CompetencyResponseDTO(
        id=competency.id.value,
        name=competency.name,
        description=competency.description,
        category_id=competency.category_id.value,
        group_id=competency.group_id.value,
        level_descriptions=competency.level_descriptions,
    )


def map_path(path: CompetencyPath) -> PathResponseDTO:
    """
    Map a career path aggregate (with levels and requirements) to its DTO.

    Args:
        path: The stored career path.

    Returns:
        The response DTO with nested levels ordered by their order value.
    """
    return PathResponseDTO(
        id=path.id.value,
        name=path.name,
        description=path.description,
        levels=[map_level(level) for level in path.levels_in_order()],
    )


def map_level(level: PathLevel) -> LevelResponseDTO:
    """
    Map a path level and its requirements to a level DTO.

    Args:
        level: A ``PathLevel`` from a career path aggregate.

    Returns:
        The level response DTO with nested requirement DTOs.
    """
    return LevelResponseDTO(
        id=level.id.value,
        name=level.name,
        order=level.order,
        requirements=[
            RequirementResponseDTO(
                competency_id=requirement.competency_id.value,
                minimum_level=requirement.minimum_level,
                weight=requirement.weight,
            )
            for requirement in level.requirements
        ],
    )


def map_enrollment(enrollment: PathEnrollment) -> EnrollmentDTO:
    """
    Map a path enrollment to its DTO.

    Args:
        enrollment: One enrollment entry from a collaborator's history.

    Returns:
        The enrollment response DTO.
    """
    return EnrollmentDTO(
        path_id=enrollment.path_id.value,
        target_level=enrollment.target_level,
        enrolled_at=enrollment.enrolled_at,
        is_active=enrollment.is_active,
    )


def map_collaborator(collaborator: Collaborator) -> CollaboratorResponseDTO:
    """
    Map a collaborator aggregate and its enrollment history to its DTO.

    Args:
        collaborator: The stored collaborator.

    Returns:
        The collaborator response DTO with nested enrollment DTOs.
    """
    return CollaboratorResponseDTO(
        id=collaborator.id.value,
        name=collaborator.name,
        email=collaborator.email,
        department=collaborator.department,
        enrollments=[map_enrollment(e) for e in collaborator.enrollments],
    )


def map_measurement(measurement: CompetencyMeasurement) -> MeasurementDTO:
    """
    Map a competency measurement to its DTO.

    Args:
        measurement: One measurement inside an evaluation.

    Returns:
        The measurement response DTO.
    """
    return MeasurementDTO(
        id=measurement.id.value,
        competency_id=measurement.competency_id.value,
        current_level=measurement.current_level,
        notes=measurement.notes,
        evidence=measurement.evidence,
    )


def map_evaluation(evaluation: Evaluation) -> EvaluationResponseDTO:
    """
    Map an evaluation aggregate and its measurements to its DTO.

    Args:
        evaluation: The stored evaluation.

    Returns:
        The evaluation response DTO with nested measurement DTOs.
    """
    return EvaluationResponseDTO(
        id=evaluation.id.value,
        collaborator_id=evaluation.collaborator_id.value,
        evaluator_id=evaluation.evaluator_id.value,
        period=evaluation.period,
        evaluation_date=evaluation.evaluation_date,
        status=evaluation.status,
        measurements=[map_measurement(m) for m in evaluation.measurements],
        submitted_at=evaluation.submitted_at,
        response_date=evaluation.response_date,
        response_notes=evaluation.response_notes,
    )


def map_gap(gap: CompetencyGap) -> CompetencyGapDTO:
    """
    Map a domain competency gap to its DTO.

    Args:
        gap: One gap produced by the gap analysis domain service.

    Returns:
        The competency gap DTO.
    """
    return CompetencyGapDTO(
        competency_id=gap.competency_id.value,
        current_level=gap.current_level,
        required_level=gap.required_level,
        gap=gap.gap,
        weight=gap.weight,
    )


def map_eligibility(eligibility: ProgressionEligibility) -> ProgressionEligibilityDTO:
    """
    Map a domain progression eligibility to its DTO.

    Args:
        eligibility: The eligibility produced by the gap analysis domain
            service.

    Returns:
        The progression eligibility DTO.
    """
    return ProgressionEligibilityDTO(
        is_eligible=eligibility.is_eligible,
        blocking_competency_ids=[
            competency_id.value for competency_id in eligibility.blocking_competency_ids
        ],
    )
