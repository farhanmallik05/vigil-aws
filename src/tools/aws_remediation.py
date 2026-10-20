"""AWS operational tools for diagnosis and incident remediation.

Implements safe diagnostics, controlled safe mutations, and high-risk destructive tools.
Decorated with `@tool` from the Strands Agents SDK.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from strands import tool

logger = logging.getLogger("vigil_aws.tools")


# ============================================================================
# Safe Diagnostic Tools (Blast Radius: harmless_read)
# ============================================================================

@tool
def describe_cloudwatch_alarms(state: str = "ALARM") -> str:
    """Retrieves all active CloudWatch alarms in the specified state.

    Args:
        state: Alarm state to filter by (e.g. 'ALARM', 'OK', 'INSUFFICIENT_DATA').

    Returns:
        JSON string listing the matching alarms, metric names, and breach details.
    """
    logger.info(f"Executing describe_cloudwatch_alarms(state='{state}')")
    alarms = [
        {
            "AlarmName": "HighMemoryUtilization-PaymentsService",
            "StateValue": state,
            "MetricName": "MemoryUtilization",
            "Namespace": "AWS/ECS",
            "Threshold": 85.0,
            "CurrentValue": 94.2,
            "Dimensions": [{"Name": "ServiceName", "Value": "payments-api"}],
            "StateReason": "Threshold Breached: Memory utilization is at 94.2% for 3 consecutive periods.",
        },
        {
            "AlarmName": "DynamoDB-ProvisionedThroughputExceeded",
            "StateValue": state,
            "MetricName": "ThrottledRequests",
            "Namespace": "AWS/DynamoDB",
            "Threshold": 5.0,
            "CurrentValue": 38.0,
            "Dimensions": [{"Name": "TableName", "Value": "production_orders"}],
            "StateReason": "Throttled requests exceeded 5 per minute on production_orders.",
        },
    ]
    return json.dumps({"status": "success", "alarms": alarms}, indent=2)


@tool
def get_service_metrics(service_name: str, metric_name: str = "MemoryUtilization", period: int = 300) -> str:
    """Queries CloudWatch metric statistics for a specific microservice.

    Args:
        service_name: Name of the microservice (e.g. 'payments-api').
        metric_name: Name of metric (e.g. 'MemoryUtilization', 'CPUUtilization', 'RequestCount').
        period: Granularity period in seconds (default 300).

    Returns:
        JSON string containing the metric timeseries data points.
    """
    logger.info(f"Executing get_service_metrics(service_name='{service_name}', metric='{metric_name}')")
    datapoints = [
        {"Timestamp": "2026-10-20T11:40:00Z", "Average": 82.1, "Unit": "Percent"},
        {"Timestamp": "2026-10-20T11:45:00Z", "Average": 88.4, "Unit": "Percent"},
        {"Timestamp": "2026-10-20T11:50:00Z", "Average": 94.2, "Unit": "Percent"},
    ]
    return json.dumps({
        "status": "success",
        "service": service_name,
        "metric": metric_name,
        "datapoints": datapoints,
        "summary": f"Service '{service_name}' exhibiting steady climb in {metric_name} approaching critical limits.",
    }, indent=2)


@tool
def check_service_health(service_name: str) -> str:
    """Performs deep health and dependency check for an ECS/EKS service.

    Args:
        service_name: Name of the microservice.

    Returns:
        JSON string describing container state, error rates, and downstream connection health.
    """
    logger.info(f"Executing check_service_health(service_name='{service_name}')")
    return json.dumps({
        "status": "degraded",
        "service": service_name,
        "running_tasks": 4,
        "desired_tasks": 4,
        "unhealthy_tasks": 2,
        "primary_error": "OutOfMemoryError: Java heap space during batch reconciliation",
        "downstream_database": "Healthy (DynamoDB: production_orders)",
        "recommendation": "Drain unhealthy tasks and rolling restart container with increased heap headroom.",
    }, indent=2)


# ============================================================================
# Safe Mutation Tools (Blast Radius: safe_mutation)
# ============================================================================

@tool
def drain_and_restart_container(cluster_name: str, service_name: str) -> str:
    """Executes a graceful rolling restart of ECS tasks for a service.

    Args:
        cluster_name: ECS cluster name (e.g. 'prod-cluster').
        service_name: ECS service name (e.g. 'payments-api').

    Returns:
        JSON string confirming rolling deployment initiation and deployment ID.
    """
    logger.info(f"Executing drain_and_restart_container(cluster='{cluster_name}', service='{service_name}')")
    return json.dumps({
        "status": "initiated",
        "action": "ROLLING_RESTART",
        "cluster": cluster_name,
        "service": service_name,
        "deployment_id": "dep-0498a9c2b4e7",
        "message": f"Successfully initiated rolling restart for '{service_name}'. New tasks launching, old tasks draining.",
    }, indent=2)


@tool
def scale_auto_scaling_group(asg_name: str, desired_capacity: int) -> str:
    """Adjusts the desired capacity of an EC2 Auto Scaling Group.

    Args:
        asg_name: Name of the Auto Scaling Group.
        desired_capacity: Target instance count.

    Returns:
        JSON string confirming capacity change.
    """
    logger.info(f"Executing scale_auto_scaling_group(asg='{asg_name}', desired={desired_capacity})")
    return json.dumps({
        "status": "updated",
        "asg": asg_name,
        "previous_capacity": desired_capacity - 2,
        "new_desired_capacity": desired_capacity,
        "message": f"Auto Scaling Group '{asg_name}' scaled to {desired_capacity} instances.",
    }, indent=2)


# ============================================================================
# High-Risk / Destructive Mutation Tools (Blast Radius: destructive_irreversible)
# ============================================================================

@tool
def terminate_ec2_instance(instance_id: str, dry_run: bool = False) -> str:
    """Permanently terminates an EC2 virtual machine instance.

    Args:
        instance_id: The AWS EC2 instance identifier (e.g. 'i-0123456789abcdef0').
        dry_run: If True, checks permissions without actually terminating.

    Returns:
        JSON string with termination status.
    """
    logger.warning(f"CRITICAL ACTION: terminate_ec2_instance(instance_id='{instance_id}', dry_run={dry_run})")
    return json.dumps({
        "status": "terminated" if not dry_run else "dry_run_passed",
        "instance_id": instance_id,
        "currentState": {"Code": 48, "Name": "terminated"},
        "previousState": {"Code": 16, "Name": "running"},
        "warning": "Instance permanently destroyed. Ephemeral disks wiped.",
    }, indent=2)


@tool
def delete_dynamodb_table(table_name: str) -> str:
    """Permanently deletes an Amazon DynamoDB table and all stored records.

    Args:
        table_name: The name of the DynamoDB table to delete.

    Returns:
        JSON string detailing the deletion status.
    """
    logger.warning(f"CRITICAL ACTION: delete_dynamodb_table(table_name='{table_name}')")
    return json.dumps({
        "status": "deleting",
        "table_name": table_name,
        "tableStatus": "DELETING",
        "warning": f"Table '{table_name}' and all partitions are marked for permanent deletion.",
    }, indent=2)


@tool
def revoke_security_group_ingress(group_id: str, cidr_ip: str, from_port: int, to_port: int) -> str:
    """Revokes an ingress network rule from an EC2/VPC Security Group.

    Args:
        group_id: Security Group ID (e.g. 'sg-0123456789abcdef0').
        cidr_ip: CIDR block to remove access for (e.g. '0.0.0.0/0').
        from_port: Starting port of the rule.
        to_port: Ending port of the rule.

    Returns:
        JSON string confirming revocation.
    """
    logger.info(f"Executing revoke_security_group_ingress(group='{group_id}', cidr='{cidr_ip}', port={from_port}-{to_port})")
    return json.dumps({
        "status": "revoked",
        "group_id": group_id,
        "revoked_rule": {"cidr": cidr_ip, "from_port": from_port, "to_port": to_port},
    }, indent=2)


# Export tool bundle for easy agent assembly
ALL_AWS_TOOLS = [
    describe_cloudwatch_alarms,
    get_service_metrics,
    check_service_health,
    drain_and_restart_container,
    scale_auto_scaling_group,
    terminate_ec2_instance,
    delete_dynamodb_table,
    revoke_security_group_ingress,
]
