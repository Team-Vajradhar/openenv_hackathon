from incident_response_env.models import IncidentResponseState


def grade_incident(state: IncidentResponseState) -> float:
    """ Grading of incident between  0 to 1"""
    if not state.resolved:
        return 0.0
    
    score = 0.4 #reward for resolution
    
    if state.logs_checked:
        score += 0.2
    
    if state.metrics_checked:
        score += 0.1

    if state.service_status == "healthy":
        score += 0.2
    
    if state.step_count <= 4:
        score += 0.1
    
    if state.scale_level > 6:
        score -= 0.1
    
    return min(score, 1.0)
    