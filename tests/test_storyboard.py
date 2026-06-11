from weaver.models.schemas import StoryboardSyncRequest, StoryboardVariables
from weaver.services.storyboard import StoryboardService
from weaver.api.main import _bootstrap_demo_state, _fresh_storyboard_service


def test_storyboard_sync_all_variables() -> None:
    service = StoryboardService(_fresh_storyboard_service)
    response = service.sync(
        StoryboardSyncRequest(
            variables=StoryboardVariables(trauma=True, walk=True, mba=True),
        )
    )
    assert len(response.metrics) == 3
    assert response.win_contribution_percent > 0
    assert response.captions.dark
    assert response.captions.bright
    assert response.element_visibility["el-dog"] == 1.0


def test_storyboard_sync_reduces_metrics_when_vars_off() -> None:
    service = StoryboardService(_fresh_storyboard_service)
    full = service.sync(
        StoryboardSyncRequest(variables=StoryboardVariables(trauma=True, walk=True, mba=True))
    )
    minimal = service.sync(
        StoryboardSyncRequest(variables=StoryboardVariables(trauma=False, walk=False, mba=False))
    )
    assert minimal.metrics[0].current_value >= full.metrics[0].current_value
