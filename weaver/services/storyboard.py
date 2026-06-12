"""Parallel-universe storyboard — maps UI variables to DAG compile + metrics."""

from __future__ import annotations

from typing import Any

from weaver.services.llm import complete_json, parse_json_text

from weaver.models.schemas import (
    CompileMutationRequest,
    StoryboardCaptions,
    StoryboardMetric,
    StoryboardSyncRequest,
    StoryboardSyncResponse,
    StoryboardVariables,
)
from weaver.services.bindings import build_render_bindings
from weaver.services.lifecycle import WeaverLifecycleService


VARIABLE_MUTATIONS: dict[str, tuple[str, dict[str, Any]]] = {
    "trauma": (
        "node_cognitive_perfectionism",
        {"self_blame": False, "perfectionism_load": 0.18, "rumination_index": 0.22},
    ),
    "walk": (
        "node_somatic_cgm",
        {"posture_compression": False, "cgm_spike_index": 0.22, "vagal_tone_deficit": 0.12},
    ),
    "mba": (
        "node_asset_snapshot",
        {"mba_completed": True, "education_debt": 0.0, "cfa_retry_count": 0},
    ),
}

VARIABLE_LABELS = {
    "trauma": "童年卡点已释放",
    "walk": "餐后散步协议",
    "mba": "MBA穿插学习",
}


class StoryboardService:
    def __init__(self, lifecycle_factory) -> None:
        self._lifecycle_factory = lifecycle_factory

    def sync(self, request: StoryboardSyncRequest) -> StoryboardSyncResponse:
        service: WeaverLifecycleService = self._lifecycle_factory()
        active = request.variables.active_keys()
        compile_trace: list[str] = []

        for key in ("trauma", "walk", "mba"):
            if not getattr(request.variables, key):
                continue
            node_id, payload = VARIABLE_MUTATIONS[key]
            result = service.compile_historical_mutation(
                CompileMutationRequest(
                    target_node_id=node_id,
                    mutated_parameters=payload,
                    mark_historical_exception=True,
                )
            )
            compile_trace.extend(result.compile_trace)

        state = service.get_current_state()
        bindings = build_render_bindings(service)
        chaos = service.evaluate_chaos(
            next(n for n in state.nodes if n.node_id == "node_macro_layoff_risk")
        )

        metrics = self._build_metrics(state, bindings, len(active))
        captions = self._template_captions(request.variables)
        win_contrib = self._win_contribution(chaos.win_rate_delta, len(active))

        return StoryboardSyncResponse(
            variables=request.variables,
            metrics=metrics,
            captions=captions,
            win_contribution_percent=win_contrib,
            computed_win_rate=chaos.computed_win_rate,
            structural_integrity=chaos.structural_integrity.value,
            compile_trace=compile_trace,
            element_visibility=self._element_visibility(request.variables),
        )

    def generate_captions(self, variables: StoryboardVariables) -> StoryboardCaptions:
        llm = self._llm_captions(variables)
        if llm is not None:
            return llm
        return self._template_captions(variables)

    @staticmethod
    def _caption_prompt(variables: StoryboardVariables) -> tuple[str, str]:
        active = variables.active_labels(VARIABLE_LABELS)
        system = (
            "你是Weaver.AI平行宇宙分镜引擎的旁白导演。用户Jennifer，单身母亲，女儿Linda现12岁"
            "（5年后17岁），住北卡Cary，管理pre-diabetes，Fidelity系统分析师。生成两段5年后(2031年)"
            "的电影旁白字幕，画面感强，具体到物件和动作，不抒情不说教。输出严格JSON无markdown："
            '{"dark":"默认时间线旁白，疲惫压抑，50字内","bright":"改写后旁白，松弛温暖，50字内"}'
        )
        user = f"已改写变量：{'、'.join(active) or '无（全部关闭）'}。生成双时间线旁白。"
        return system, user

    @staticmethod
    def _parse_caption_json(text: str) -> StoryboardCaptions | None:
        parsed = parse_json_text(text)
        if parsed is None:
            return None
        dark = str(parsed.get("dark", "")).strip()
        bright = str(parsed.get("bright", "")).strip()
        if not dark and not bright:
            return None
        return StoryboardCaptions(dark=dark, bright=bright)

    def _build_metrics(
        self,
        state,
        bindings: dict[str, Any],
        active_count: int,
    ) -> list[StoryboardMetric]:
        cgm = float(bindings["somatic_channel"]["VAR_SOM_CGM"])
        glucose_base, glucose_best = 128, 94
        glucose_now = round(glucose_base - (glucose_base - glucose_best) * (1.0 - cgm) * (active_count / 3))

        cortisol_agg = float(bindings["system_stress"]["aggregate_cortisol"])
        cortisol_base, cortisol_best = 82, 31
        cortisol_now = round(cortisol_base - (cortisol_base - cortisol_best) * (1.0 - cortisol_agg) * (active_count / 3))

        relational = next(
            (n for n in state.nodes if n.node_id == "node_relational_boundary"),
            None,
        )
        rel_stress = relational.cortisol_impact if relational else 0.35
        rel_base, rel_best = 38, 88
        rel_now = round(rel_base + (rel_best - rel_base) * (1.0 - rel_stress) * (active_count / 3))

        return [
            StoryboardMetric(
                name="空腹血糖 mg/dL",
                base_value=glucose_base,
                current_value=glucose_now,
                unit="",
                inverse=True,
                max_value=140,
            ),
            StoryboardMetric(
                name="夜间皮质醇水平",
                base_value=cortisol_base,
                current_value=cortisol_now,
                unit="%",
                inverse=True,
                max_value=100,
            ),
            StoryboardMetric(
                name="亲子关系温度",
                base_value=rel_base,
                current_value=rel_now,
                unit="°",
                inverse=False,
                max_value=100,
            ),
        ]

    def _win_contribution(self, win_rate_delta: float, active_count: int) -> float:
        engine_lift = max(0.0, win_rate_delta * 100.0)
        tier_lift = [0.0, 3.1, 6.2, 9.4][active_count]
        return round(min(12.0, tier_lift * 0.55 + engine_lift * 4.0), 1)

    @staticmethod
    def _element_visibility(variables: StoryboardVariables) -> dict[str, float]:
        return {
            "el-mom-b": 1.0 if variables.trauma else 0.12,
            "el-linda": 1.0 if variables.trauma else 0.12,
            "el-dog": 1.0 if variables.walk else 0.12,
            "el-diploma": 1.0 if variables.mba else 0.12,
        }

    def _template_captions(self, variables: StoryboardVariables) -> StoryboardCaptions:
        active = variables.active_labels(VARIABLE_LABELS)
        if not active:
            return StoryboardCaptions(
                dark="深夜十一点半。第三次重考CFA的题库还亮着，两瓶药放在手边。女儿的房门上挂着「勿扰」，已经一周没说过十句话。",
                bright="变量全部关闭——引擎仅保留默认时间线基线。擦动分割线查看未改写状态。",
            )
        if variables.trauma and variables.walk and variables.mba:
            return StoryboardCaptions(
                dark="凌晨的台灯下，题库翻到第三遍，药瓶和冷掉的咖啡挤在一起。隔壁房门紧闭，今天母女只说了四个字。",
                bright="傍晚六点半的金色光线里，切菜声和Linda的歌声混在一起。冰箱上贴着下个月的母女公路旅行计划，墙上是MBA毕业证。",
            )
        return StoryboardCaptions(
            dark="雨夜窗前，CFA二级模考红灯未灭。母亲背影弓在书桌前，客厅只剩挂钟和药片碰撞杯壁的声音。",
            bright=f"改写变量：{'、'.join(active)}。厨房有热气，窗外天色柔和，关系线不再绷成钢丝。",
        )

    def _llm_captions(self, variables: StoryboardVariables) -> StoryboardCaptions | None:
        system, user = self._caption_prompt(variables)
        parsed = complete_json(system, user, max_tokens=500)
        if parsed is None:
            return None
        dark = str(parsed.get("dark", "")).strip()
        bright = str(parsed.get("bright", "")).strip()
        if not dark and not bright:
            return None
        return StoryboardCaptions(dark=dark, bright=bright)
