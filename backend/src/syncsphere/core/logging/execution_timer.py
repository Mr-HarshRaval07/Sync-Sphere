import time
import logging
from typing import List, Tuple

logger = logging.getLogger("syncsphere.timing")


class ExecutionTimer:
    """
    Tracks execution stage durations in milliseconds and logs a formatted timing summary.
    Emits a WARNING log if any single stage exceeds 5000 ms.
    """
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = time.perf_counter()
        self.stages: List[Tuple[str, float]] = []

    def record_stage(self, stage_name: str, duration_ms: float):
        """Record an explicit stage duration in milliseconds."""
        dur = float(duration_ms)
        self.stages.append((stage_name, dur))
        if dur > 5000.0:
            logger.warning(
                "[PERFORMANCE WARNING] Stage '%s' took %.1f ms (> 5000 ms) in %s",
                stage_name, dur, self.operation_name
            )

    def print_summary(self) -> float:
        """
        Prints and logs a formatted timing summary showing each stage duration
        and the total end-to-end task duration.
        """
        total_duration_ms = (time.perf_counter() - self.start_time) * 1000.0

        lines = [
            "================================================================================",
            f"[TIMING SUMMARY] {self.operation_name} (Total: {total_duration_ms:.1f} ms)",
            "--------------------------------------------------------------------------------"
        ]

        for idx, (stage_name, dur) in enumerate(self.stages, 1):
            warn_flag = " [!] SLOW (> 5s)" if dur > 5000.0 else ""
            lines.append(f"{idx:2d}. {stage_name:<46} : {dur:>8.1f} ms{warn_flag}")

        lines.append("--------------------------------------------------------------------------------")

        for stage_name, dur in self.stages:
            if dur > 5000.0:
                lines.append(f"[PERFORMANCE WARNING] Stage '{stage_name}' took {dur:.1f} ms (> 5000 ms)")

        lines.append("================================================================================")

        summary_str = "\n".join(lines)
        logger.info(summary_str)
        print(summary_str)
        return total_duration_ms
