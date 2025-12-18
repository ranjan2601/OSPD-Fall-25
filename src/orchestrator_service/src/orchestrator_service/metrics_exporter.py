"""Google Cloud Monitoring metrics exporter.

This module exports application metrics to Google Cloud Monitoring
to populate the Terraform-defined custom metrics and dashboard.
"""

import logging
import os
import time
from typing import Any

from google.cloud import monitoring_v3
from google.protobuf import timestamp_pb2

logger = logging.getLogger(__name__)


class MetricsExporter:
    """Exports metrics to Google Cloud Monitoring."""

    def __init__(self, project_id: str | None = None) -> None:
        """Initialize the metrics exporter.

        Args:
            project_id: GCP project ID. If None, uses GCP_PROJECT env var.
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT")
        if not self.project_id:
            logger.warning("No GCP_PROJECT set - metrics export disabled")
            self.client = None
            return

        try:
            self.client = monitoring_v3.MetricServiceClient()
            self.project_name = f"projects/{self.project_id}"
            logger.info(f"Metrics exporter initialized for project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize monitoring client: {e}")
            self.client = None

    def export_metrics(self, metrics: dict[str, Any]) -> None:
        """Export orchestrator metrics to Cloud Monitoring.

        Args:
            metrics: Dictionary of metrics from orchestrator.get_metrics()
        """
        if not self.client:
            return

        try:
            current_time = time.time()

            if metrics.get("average_latency_seconds", 0) > 0:
                self._write_metric(
                    metric_type="custom.googleapis.com/ai_chat/request_latency",
                    value=metrics["average_latency_seconds"] * 1000,
                    labels={"service": "orchestrator", "operation": "handle_message"},
                    timestamp=current_time,
                )

            if metrics.get("total_requests", 0) > 0:
                success_rate = metrics.get("success_rate", 0) * 100
                self._write_metric(
                    metric_type="custom.googleapis.com/ai_chat/success_rate",
                    value=success_rate,
                    labels={"service": "orchestrator"},
                    timestamp=current_time,
                )

                failure_rate = metrics.get("failure_rate", 0) * 100
                self._write_metric(
                    metric_type="custom.googleapis.com/ai_chat/failure_rate",
                    value=failure_rate,
                    labels={"service": "orchestrator"},
                    timestamp=current_time,
                )

            logger.debug(
                f"Exported metrics - latency: {metrics.get('average_latency_seconds', 0) * 1000:.2f}ms, "
                f"success: {metrics.get('success_rate', 0) * 100:.1f}%, "
                f"failure: {metrics.get('failure_rate', 0) * 100:.1f}%"
            )

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")

    def _write_metric(
        self,
        metric_type: str,
        value: float,
        labels: dict[str, str],
        timestamp: float,
    ) -> None:
        """Write a single metric to Cloud Monitoring.

        Args:
            metric_type: Full metric type string
            value: Metric value
            labels: Metric labels
            timestamp: Unix timestamp
        """
        if not self.client:
            return

        series = monitoring_v3.TimeSeries()
        series.metric.type = metric_type
        series.resource.type = "global"

        for key, val in labels.items():
            series.metric.labels[key] = val

        now = timestamp_pb2.Timestamp()
        now.seconds = int(timestamp)
        now.nanos = int((timestamp - int(timestamp)) * 1e9)

        interval = monitoring_v3.TimeInterval({"end_time": now})
        point = monitoring_v3.Point(
            {
                "interval": interval,
                "value": {"double_value": value},
            }
        )

        series.points = [point]

        try:
            self.client.create_time_series(name=self.project_name, time_series=[series])
            logger.debug(f"Successfully wrote metric {metric_type} = {value}")
        except Exception as e:
            logger.error(f"Failed to write metric {metric_type}: {e}")
            raise


_exporter: MetricsExporter | None = None


def get_metrics_exporter() -> MetricsExporter:
    """Get or create the global metrics exporter.

    Returns:
        MetricsExporter instance
    """
    global _exporter
    if _exporter is None:
        _exporter = MetricsExporter()
    return _exporter
