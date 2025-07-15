"""
Pipeline monitoring and status API endpoints
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from ..services.cache import CacheService

logger = logging.getLogger(__name__)

from ..config.settings import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])

# In-memory storage for pipeline status (in production, use Redis)
pipeline_status_cache = {}


class PipelineStatusUpdate(BaseModel):
    commit: str
    status: str  # success, failure, cancelled, in_progress
    branch: str
    workflow: str
    timestamp: str
    repository: str
    details: Optional[Dict] = None


class DeploymentStatus(BaseModel):
    commit: str
    status: str  # pending, in_progress, success, failure
    environment: str = "production"
    url: Optional[str] = None
    timestamp: str
    build_time: Optional[str] = None


@router.post("/pipeline-status")
async def update_pipeline_status(
    status_update: PipelineStatusUpdate,
    background_tasks: BackgroundTasks,
    request: Request,
):
    """
    Webhook endpoint for GitHub Actions to report pipeline status
    """
    try:
        # Store status in cache
        cache_key = f"pipeline_status:{status_update.commit}"
        status_data = {
            "commit": status_update.commit,
            "status": status_update.status,
            "branch": status_update.branch,
            "workflow": status_update.workflow,
            "timestamp": status_update.timestamp,
            "repository": status_update.repository,
            "details": status_update.details or {},
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Store in both memory and Redis cache
        pipeline_status_cache[status_update.commit] = status_data

        cache_service = CacheService()
        await cache_service.set(
            cache_key, json.dumps(status_data), expire=86400
        )  # 24 hours

        logger.info(
            f"Pipeline status updated: {status_update.commit} -> {status_update.status}"
        )

        # Trigger background processing if needed
        if status_update.status == "success" and status_update.branch == "main":
            background_tasks.add_task(monitor_deployment, status_update.commit)

        return {"status": "received", "commit": status_update.commit}

    except Exception as e:
        logger.error(f"Failed to update pipeline status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update pipeline status")


@router.get("/status/{commit}")
async def get_pipeline_status(commit: str):
    """
    Get pipeline status for a specific commit
    """
    try:
        # Check memory cache first
        if commit in pipeline_status_cache:
            status_data = pipeline_status_cache[commit]
        else:
            # Check Redis cache
            cache_service = CacheService()
            cache_key = f"pipeline_status:{commit}"
            cached_data = await cache_service.get(cache_key)

            if cached_data:
                status_data = json.loads(cached_data)
                # Update memory cache
                pipeline_status_cache[commit] = status_data
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"No pipeline status found for commit {commit}",
                )

        # Check if status is stale (older than 1 hour)
        timestamp = datetime.fromisoformat(
            status_data["timestamp"].replace("Z", "+00:00")
        )
        if datetime.utcnow().replace(tzinfo=timestamp.tzinfo) - timestamp > timedelta(
            hours=1
        ):
            status_data["is_stale"] = True
            status_data["warning"] = "Pipeline data is stale"

        return status_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline status for {commit}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve pipeline status"
        )


@router.get("/status")
async def get_recent_pipeline_status(limit: int = 10):
    """
    Get recent pipeline status for all commits
    """
    try:
        # Get all statuses from memory cache
        all_statuses = list(pipeline_status_cache.values())

        # Sort by timestamp (newest first)
        all_statuses.sort(
            key=lambda x: datetime.fromisoformat(x["timestamp"].replace("Z", "+00:00")),
            reverse=True,
        )

        # Return limited results
        return {"statuses": all_statuses[:limit], "total": len(all_statuses)}

    except Exception as e:
        logger.error(f"Failed to get recent pipeline status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve pipeline status"
        )


@router.post("/deployment-status")
async def update_deployment_status(deployment: DeploymentStatus):
    """
    Update deployment status for a specific commit
    """
    try:
        cache_key = f"deployment_status:{deployment.commit}"
        status_data = {
            "commit": deployment.commit,
            "status": deployment.status,
            "environment": deployment.environment,
            "url": deployment.url,
            "timestamp": deployment.timestamp,
            "build_time": deployment.build_time,
            "updated_at": datetime.utcnow().isoformat(),
        }

        cache_service = CacheService()
        await cache_service.set(cache_key, json.dumps(status_data), expire=86400)

        logger.info(
            f"Deployment status updated: {deployment.commit} -> {deployment.status}"
        )

        return {"status": "received", "commit": deployment.commit}

    except Exception as e:
        logger.error(f"Failed to update deployment status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update deployment status"
        )


@router.get("/deployment-status/{commit}")
async def get_deployment_status(commit: str):
    """
    Get deployment status for a specific commit
    """
    try:
        cache_service = CacheService()
        cache_key = f"deployment_status:{commit}"
        cached_data = await cache_service.get(cache_key)

        if cached_data:
            return json.loads(cached_data)
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No deployment status found for commit {commit}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment status for {commit}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve deployment status"
        )


@router.get("/health-check")
async def pipeline_health_check():
    """
    Health check endpoint for pipeline monitoring system
    """
    try:
        # Check if pipeline monitoring is working
        recent_statuses = len(pipeline_status_cache)

        # Check Redis connectivity
        cache_service = CacheService()
        test_key = "pipeline_health_test"
        await cache_service.set(test_key, "test", expire=60)
        test_value = await cache_service.get(test_key)

        redis_healthy = test_value == "test"

        return {
            "status": "healthy",
            "pipeline_monitoring": True,
            "recent_pipelines": recent_statuses,
            "redis_connectivity": redis_healthy,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Pipeline health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


async def monitor_deployment(commit: str):
    """
    Background task to monitor deployment after successful pipeline
    """
    try:
        logger.info(f"Starting deployment monitoring for commit {commit}")

        # Update deployment status to in_progress
        deployment_status = DeploymentStatus(
            commit=commit,
            status="in_progress",
            environment="production",
            url=settings.production_url,
            timestamp=datetime.utcnow().isoformat(),
        )

        await update_deployment_status(deployment_status)

        # Here you would typically check Watchtower logs or container status
        # For now, we'll simulate monitoring
        logger.info(f"Monitoring deployment progress for commit {commit}")

    except Exception as e:
        logger.error(f"Failed to monitor deployment for {commit}: {e}")


@router.get("/metrics")
async def get_pipeline_metrics():
    """
    Get pipeline performance metrics
    """
    try:
        # Calculate metrics from stored statuses
        all_statuses = list(pipeline_status_cache.values())

        # Filter last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_statuses = [
            status
            for status in all_statuses
            if datetime.fromisoformat(status["timestamp"].replace("Z", "+00:00"))
            > cutoff_time.replace(tzinfo=None)
        ]

        total_pipelines = len(recent_statuses)
        successful_pipelines = len(
            [s for s in recent_statuses if s["status"] == "success"]
        )
        failed_pipelines = len([s for s in recent_statuses if s["status"] == "failure"])

        success_rate = (
            (successful_pipelines / total_pipelines * 100) if total_pipelines > 0 else 0
        )

        return {
            "period": "24_hours",
            "total_pipelines": total_pipelines,
            "successful_pipelines": successful_pipelines,
            "failed_pipelines": failed_pipelines,
            "success_rate": round(success_rate, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get pipeline metrics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve pipeline metrics"
        )
