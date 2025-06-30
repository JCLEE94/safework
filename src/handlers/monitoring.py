"""
모니터링 API 엔드포인트
Monitoring API endpoints for real-time system metrics
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import asyncio
import subprocess
import os
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


# ============================
# 도커 컨테이너 로그 관리 엔드포인트
# ============================

@router.get("/docker/containers")
async def list_docker_containers():
    """실행 중인 도커 컨테이너 목록 조회"""
    try:
        # docker ps 명령어로 컨테이너 목록 조회
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Docker 명령어 실행 실패: {result.stderr}")
        
        lines = result.stdout.strip().split('\n')
        containers = []
        
        # 첫 번째 줄은 헤더이므로 건너뛰기
        for line in lines[1:] if len(lines) > 1 else []:
            parts = line.split('\t')
            if len(parts) >= 4:
                containers.append({
                    "id": parts[0],
                    "name": parts[1], 
                    "status": parts[2],
                    "ports": parts[3]
                })
        
        return {
            "total": len(containers),
            "containers": containers,
            "timestamp": datetime.now().isoformat()
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Docker 명령어 타임아웃")
    except Exception as e:
        logger.error(f"컨테이너 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"컨테이너 목록 조회 실패: {str(e)}")


async def stream_logs_generator(container_name: str, lines: int, since: Optional[str]) -> AsyncGenerator[str, None]:
    """로그 스트리밍을 위한 비동기 제너레이터"""
    cmd = ["docker", "logs", "--follow", "--tail", str(lines), "--timestamps"]
    
    if since:
        cmd.extend(["--since", since])
    
    cmd.append(container_name)
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        # 초기 메시지
        yield f"data: {json.dumps({'type': 'connected', 'container': container_name, 'message': f'{container_name} 로그 스트리밍 시작'})}\n\n"
        
        while True:
            line = await process.stdout.readline()
            if line:
                log_line = line.decode('utf-8').strip()
                yield f"data: {json.dumps({'type': 'log', 'container': container_name, 'line': log_line, 'timestamp': datetime.now().isoformat()})}\n\n"
            else:
                # 프로세스가 종료됨
                break
                
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    finally:
        if 'process' in locals():
            try:
                process.terminate()
                await process.wait()
            except:
                pass


@router.get("/docker/logs/{container_name}")
async def get_container_logs(
    container_name: str,
    lines: int = Query(default=100, ge=1, le=1000, description="가져올 로그 라인 수 (1-1000)"),
    follow: bool = Query(default=False, description="실시간 로그 스트리밍 여부"),
    since: Optional[str] = Query(default=None, description="특정 시간 이후 로그 (예: 2h, 1d)")
):
    """특정 컨테이너의 로그 조회 (스트리밍 지원)"""
    try:
        # 실시간 스트리밍 요청인 경우
        if follow:
            return StreamingResponse(
                stream_logs_generator(container_name, lines, since),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # nginx 버퍼링 비활성화
                }
            )
        
        # 일반 로그 조회
        cmd = ["docker", "logs", "--tail", str(lines), "--timestamps"]
        
        if since:
            cmd.extend(["--since", since])
            
        cmd.append(container_name)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=404, detail=f"컨테이너를 찾을 수 없거나 로그 조회 실패: {result.stderr}")
        
        log_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        return {
            "container": container_name,
            "lines_requested": lines,
            "lines_returned": len(log_lines),
            "logs": log_lines,
            "timestamp": datetime.now().isoformat(),
            "since": since
        }
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="로그 조회 타임아웃")
    except Exception as e:
        logger.error(f"컨테이너 로그 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"로그 조회 실패: {str(e)}")


@router.get("/docker/stats/{container_name}")
async def get_container_stats(container_name: str):
    """특정 컨테이너의 리소스 사용량 통계"""
    try:
        # docker stats 명령어로 컨테이너 통계 조회 (--no-stream으로 한 번만)
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", 
             "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}", 
             container_name],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=404, detail=f"컨테이너를 찾을 수 없음: {result.stderr}")
        
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            raise HTTPException(status_code=404, detail="컨테이너 통계를 가져올 수 없음")
        
        # 두 번째 줄이 실제 데이터
        stats_line = lines[1].split('\t')
        if len(stats_line) >= 6:
            return {
                "container": stats_line[0],
                "cpu_percent": stats_line[1],
                "memory_usage": stats_line[2],
                "memory_percent": stats_line[3],
                "network_io": stats_line[4],
                "block_io": stats_line[5],
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="통계 데이터 파싱 실패")
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="통계 조회 타임아웃")
    except Exception as e:
        logger.error(f"컨테이너 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.websocket("/docker/logs/stream/{container_name}")
async def stream_container_logs(websocket: WebSocket, container_name: str):
    """실시간 컨테이너 로그 스트리밍 (WebSocket)"""
    await websocket.accept()
    
    try:
        # docker logs --follow 명령어로 실시간 로그 스트리밍
        process = subprocess.Popen(
            ["docker", "logs", "--follow", "--timestamps", "--tail", "50", container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 연결 성공 메시지
        await websocket.send_json({
            "type": "connected",
            "container": container_name,
            "message": f"{container_name} 컨테이너 로그 스트리밍 시작"
        })
        
        # 로그 스트리밍
        while True:
            line = process.stdout.readline()
            if line:
                await websocket.send_json({
                    "type": "log",
                    "container": container_name,
                    "line": line.strip(),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # 프로세스가 종료됨
                break
                
            # WebSocket 연결 상태 확인
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
            except asyncio.TimeoutError:
                # 타임아웃은 정상 (클라이언트가 메시지를 보내지 않음)
                continue
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info(f"로그 스트리밍 WebSocket 연결 종료: {container_name}")
    except Exception as e:
        logger.error(f"로그 스트리밍 에러: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"로그 스트리밍 에러: {str(e)}"
            })
        except:
            pass
    finally:
        # 프로세스 정리
        try:
            if 'process' in locals():
                process.terminate()
                process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass


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
