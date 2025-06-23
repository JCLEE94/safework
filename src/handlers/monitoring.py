"""
모니터링 API 엔드포인트
Monitoring API endpoints for real-time system metrics
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime

from ..services.monitoring import get_metrics_collector, MetricsCollector
from ..utils.logger import logger


router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket 연결 추가: 총 {len(self.active_connections)}개 연결")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket 연결 제거: 총 {len(self.active_connections)}개 연결")
    
    async def broadcast(self, message: dict):
        """모든 연결된 클라이언트에 메시지 전송"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket 전송 실패: {e}")
                disconnected.append(connection)
        
        # 끊어진 연결 제거
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.get("/metrics/current")
async def get_current_metrics(
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """현재 시스템 메트릭 조회"""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="모니터링 서비스가 초기화되지 않았습니다")
    
    metrics = await metrics_collector.collect_system_metrics()
    app_metrics = await metrics_collector.get_application_metrics()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "system": metrics.get("system", {}),
        "process": metrics.get("process", {}),
        "application": app_metrics
    }


@router.get("/metrics/history")
async def get_metrics_history(
    minutes: int = 5,
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """최근 N분간 메트릭 히스토리 조회"""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="모니터링 서비스가 초기화되지 않았습니다")
    
    if minutes < 1 or minutes > 60:
        raise HTTPException(status_code=400, detail="minutes는 1-60 사이여야 합니다")
    
    history = metrics_collector.get_recent_metrics(minutes)
    
    return {
        "period_minutes": minutes,
        "count": len(history),
        "metrics": history
    }


@router.get("/alerts")
async def get_alerts(
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """시스템 알림 조회"""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="모니터링 서비스가 초기화되지 않았습니다")
    
    alerts = metrics_collector.get_alerts()
    
    # 심각도별 그룹화
    grouped_alerts = {
        "critical": [],
        "warning": [],
        "info": []
    }
    
    for alert in alerts:
        severity = alert.get("severity", "info")
        grouped_alerts[severity].append(alert)
    
    return {
        "total": len(alerts),
        "alerts": grouped_alerts,
        "latest": alerts[-10:] if alerts else []
    }


@router.get("/health")
async def get_health_status(
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """시스템 헬스 상태 조회"""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="모니터링 서비스가 초기화되지 않았습니다")
    
    health = await metrics_collector.get_health_status()
    
    return health


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """실시간 메트릭 스트리밍 WebSocket 엔드포인트"""
    await manager.connect(websocket)
    metrics_collector = get_metrics_collector()
    
    if not metrics_collector:
        await websocket.send_json({
            "error": "모니터링 서비스가 초기화되지 않았습니다"
        })
        manager.disconnect(websocket)
        return
    
    try:
        # 초기 데이터 전송
        initial_data = await metrics_collector.collect_system_metrics()
        await websocket.send_json({
            "type": "initial",
            "data": initial_data
        })
        
        # 실시간 메트릭 스트리밍
        while True:
            # 5초마다 메트릭 전송
            await asyncio.sleep(5)
            
            metrics = await metrics_collector.collect_system_metrics()
            app_metrics = await metrics_collector.get_application_metrics()
            
            message = {
                "type": "update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "system": metrics.get("system", {}),
                    "process": metrics.get("process", {}),
                    "application": app_metrics
                }
            }
            
            await websocket.send_json(message)
            
            # 알림이 있으면 즉시 전송
            recent_alerts = metrics_collector.get_alerts()
            if recent_alerts:
                # 마지막으로 전송한 알림 이후의 새 알림만 전송
                new_alerts = []  # 실제 구현에서는 타임스탬프 비교
                if new_alerts:
                    await websocket.send_json({
                        "type": "alert",
                        "data": new_alerts
                    })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket 클라이언트 연결 종료")
    except Exception as e:
        logger.error(f"WebSocket 에러: {e}")
        manager.disconnect(websocket)


@router.post("/alerts/threshold")
async def update_alert_threshold(
    metric_name: str,
    threshold: float,
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """알림 임계값 업데이트"""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="모니터링 서비스가 초기화되지 않았습니다")
    
    if metric_name not in metrics_collector.alert_thresholds:
        raise HTTPException(status_code=400, detail=f"알 수 없는 메트릭: {metric_name}")
    
    if threshold <= 0:
        raise HTTPException(status_code=400, detail="임계값은 0보다 커야 합니다")
    
    old_threshold = metrics_collector.alert_thresholds[metric_name]
    metrics_collector.alert_thresholds[metric_name] = threshold
    
    logger.info(f"알림 임계값 변경: {metric_name} {old_threshold} -> {threshold}")
    
    return {
        "metric": metric_name,
        "old_threshold": old_threshold,
        "new_threshold": threshold,
        "updated_at": datetime.now().isoformat()
    }


@router.get("/stats/summary")
async def get_monitoring_summary(
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """모니터링 요약 정보"""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="모니터링 서비스가 초기화되지 않았습니다")
    
    # 최근 30분 메트릭으로 요약 생성
    recent_metrics = metrics_collector.get_recent_metrics(30)
    
    if not recent_metrics:
        return {
            "message": "충분한 데이터가 수집되지 않았습니다",
            "data_points": 0
        }
    
    # CPU 사용률 통계
    cpu_values = [m['system']['cpu']['percent'] for m in recent_metrics if 'system' in m]
    
    # 메모리 사용률 통계
    memory_values = [m['system']['memory']['percent'] for m in recent_metrics if 'system' in m]
    
    # 디스크 사용률 (보통 변화가 적음)
    disk_values = [m['system']['disk']['percent'] for m in recent_metrics if 'system' in m]
    
    def calculate_stats(values):
        if not values:
            return {"min": 0, "max": 0, "avg": 0, "current": 0}
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "current": values[-1] if values else 0
        }
    
    return {
        "period": "30분",
        "data_points": len(recent_metrics),
        "cpu": calculate_stats(cpu_values),
        "memory": calculate_stats(memory_values),
        "disk": calculate_stats(disk_values),
        "alerts_count": len(metrics_collector.get_alerts()),
        "updated_at": datetime.now().isoformat()
    }


# 주기적으로 연결된 클라이언트에 브로드캐스트
async def broadcast_metrics():
    """모든 WebSocket 클라이언트에 메트릭 브로드캐스트"""
    metrics_collector = get_metrics_collector()
    if not metrics_collector:
        return
    
    while True:
        try:
            if manager.active_connections:
                metrics = await metrics_collector.collect_system_metrics()
                await manager.broadcast({
                    "type": "metrics",
                    "timestamp": datetime.now().isoformat(),
                    "data": metrics
                })
            await asyncio.sleep(5)  # 5초마다 브로드캐스트
        except Exception as e:
            logger.error(f"브로드캐스트 에러: {e}")
            await asyncio.sleep(30)
