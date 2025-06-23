"""
실시간 모니터링 서비스
Real-time monitoring service for system metrics and performance
"""

import asyncio
import json
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque, defaultdict
import redis.asyncio as redis

from ..config.settings import get_settings
from ..utils.logger import logger

settings = get_settings()


class MetricsCollector:
    """시스템 메트릭 수집기"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics_buffer = deque(maxlen=1000)  # 최근 1000개 메트릭 저장
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'response_time_ms': 2000.0,
            'error_rate': 0.05  # 5%
        }
        self.alerts = deque(maxlen=100)  # 최근 100개 알림 저장
        
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """시스템 메트릭 수집"""
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            
            # 네트워크 I/O
            net_io = psutil.net_io_counters()
            
            # 프로세스 정보
            process = psutil.Process()
            process_info = {
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(interval=1),
                'num_threads': process.num_threads(),
                'num_fds': process.num_fds() if hasattr(process, 'num_fds') else None
            }
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu': {
                        'percent': cpu_percent,
                        'count': cpu_count,
                        'per_cpu': psutil.cpu_percent(percpu=True)
                    },
                    'memory': {
                        'percent': memory.percent,
                        'used_mb': memory.used / 1024 / 1024,
                        'available_mb': memory.available / 1024 / 1024,
                        'total_mb': memory.total / 1024 / 1024
                    },
                    'disk': {
                        'percent': disk.percent,
                        'used_gb': disk.used / 1024 / 1024 / 1024,
                        'free_gb': disk.free / 1024 / 1024 / 1024,
                        'total_gb': disk.total / 1024 / 1024 / 1024
                    },
                    'network': {
                        'bytes_sent': net_io.bytes_sent,
                        'bytes_recv': net_io.bytes_recv,
                        'packets_sent': net_io.packets_sent,
                        'packets_recv': net_io.packets_recv
                    }
                },
                'process': process_info
            }
            
            # Redis에 저장
            if self.redis_client:
                await self._store_metrics_in_redis(metrics)
            
            # 버퍼에 추가
            self.metrics_buffer.append(metrics)
            
            # 임계값 체크
            await self._check_thresholds(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error("메트릭 수집 실패", error=e)
            return {}
    
    async def _store_metrics_in_redis(self, metrics: Dict[str, Any]):
        """Redis에 메트릭 저장"""
        try:
            # 시계열 데이터로 저장
            key = f"metrics:{datetime.now().strftime('%Y%m%d:%H')}"
            await self.redis_client.zadd(
                key,
                {json.dumps(metrics): time.time()}
            )
            # 24시간 후 만료
            await self.redis_client.expire(key, 86400)
        except Exception as e:
            logger.error("Redis 메트릭 저장 실패", error=e)
    
    async def _check_thresholds(self, metrics: Dict[str, Any]):
        """임계값 체크 및 알림 생성"""
        alerts = []
        
        # CPU 사용률 체크
        cpu_percent = metrics['system']['cpu']['percent']
        if cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning',
                'message': f'CPU 사용률이 {cpu_percent:.1f}%로 높습니다',
                'value': cpu_percent,
                'threshold': self.alert_thresholds['cpu_percent']
            })
        
        # 메모리 사용률 체크
        memory_percent = metrics['system']['memory']['percent']
        if memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning',
                'message': f'메모리 사용률이 {memory_percent:.1f}%로 높습니다',
                'value': memory_percent,
                'threshold': self.alert_thresholds['memory_percent']
            })
        
        # 디스크 사용률 체크
        disk_percent = metrics['system']['disk']['percent']
        if disk_percent > self.alert_thresholds['disk_percent']:
            alerts.append({
                'type': 'disk_high',
                'severity': 'critical',
                'message': f'디스크 사용률이 {disk_percent:.1f}%로 매우 높습니다',
                'value': disk_percent,
                'threshold': self.alert_thresholds['disk_percent']
            })
        
        # 알림 저장
        for alert in alerts:
            alert['timestamp'] = datetime.now().isoformat()
            self.alerts.append(alert)
            logger.warning(f"시스템 알림: {alert['message']}", **alert)
    
    async def get_application_metrics(self) -> Dict[str, Any]:
        """애플리케이션 메트릭 수집"""
        try:
            # Redis에서 최근 API 메트릭 가져오기
            if self.redis_client:
                # 최근 1시간 API 호출 통계
                api_stats = await self._get_api_statistics()
                
                # 에러율 계산
                error_rate = await self._calculate_error_rate()
                
                # 평균 응답 시간
                avg_response_time = await self._calculate_avg_response_time()
                
                return {
                    'api_calls': api_stats,
                    'error_rate': error_rate,
                    'avg_response_time_ms': avg_response_time,
                    'active_connections': await self._get_active_connections(),
                    'cache_hit_rate': await self._calculate_cache_hit_rate()
                }
            
            return {}
            
        except Exception as e:
            logger.error("애플리케이션 메트릭 수집 실패", error=e)
            return {}
    
    async def _get_api_statistics(self) -> Dict[str, Any]:
        """API 호출 통계"""
        # 로그 파일에서 API 호출 통계 수집
        # 실제 구현에서는 로그 파일 파싱 또는 Redis 카운터 사용
        return {
            'total_calls': 0,
            'calls_per_minute': 0,
            'top_endpoints': []
        }
    
    async def _calculate_error_rate(self) -> float:
        """에러율 계산"""
        # 최근 5분간 에러율 계산
        return 0.0
    
    async def _calculate_avg_response_time(self) -> float:
        """평균 응답 시간 계산"""
        # 최근 5분간 평균 응답 시간
        return 0.0
    
    async def _get_active_connections(self) -> int:
        """활성 연결 수"""
        # WebSocket 연결 수 등
        return 0
    
    async def _calculate_cache_hit_rate(self) -> float:
        """캐시 히트율 계산"""
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                hits = info.get('keyspace_hits', 0)
                misses = info.get('keyspace_misses', 0)
                total = hits + misses
                if total > 0:
                    return (hits / total) * 100
            except:
                pass
        return 0.0
    
    def get_recent_metrics(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """최근 N분간 메트릭 반환"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = []
        
        for metric in self.metrics_buffer:
            metric_time = datetime.fromisoformat(metric['timestamp'])
            if metric_time > cutoff_time:
                recent_metrics.append(metric)
        
        return recent_metrics
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """최근 알림 반환"""
        return list(self.alerts)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """전체 시스템 헬스 상태"""
        current_metrics = await self.collect_system_metrics()
        app_metrics = await self.get_application_metrics()
        
        # 전체 상태 판단
        status = 'healthy'
        issues = []
        
        if current_metrics.get('system', {}).get('cpu', {}).get('percent', 0) > 90:
            status = 'degraded'
            issues.append('CPU 사용률 과다')
        
        if current_metrics.get('system', {}).get('memory', {}).get('percent', 0) > 90:
            status = 'degraded'
            issues.append('메모리 사용률 과다')
        
        if app_metrics.get('error_rate', 0) > 0.1:  # 10% 이상
            status = 'unhealthy'
            issues.append('높은 에러율')
        
        return {
            'status': status,
            'issues': issues,
            'system_metrics': current_metrics,
            'application_metrics': app_metrics,
            'recent_alerts': self.get_alerts()[-5:]  # 최근 5개 알림
        }


# 전역 메트릭 수집기 인스턴스
metrics_collector = None


async def initialize_monitoring(redis_client: Optional[redis.Redis] = None):
    """모니터링 시스템 초기화"""
    global metrics_collector
    metrics_collector = MetricsCollector(redis_client)
    
    # 백그라운드 메트릭 수집 시작
    asyncio.create_task(collect_metrics_background())


async def collect_metrics_background():
    """백그라운드에서 주기적으로 메트릭 수집"""
    while True:
        try:
            if metrics_collector:
                await metrics_collector.collect_system_metrics()
            await asyncio.sleep(30)  # 30초마다 수집
        except Exception as e:
            logger.error("백그라운드 메트릭 수집 실패", error=e)
            await asyncio.sleep(60)  # 에러 시 1분 대기


def get_metrics_collector() -> MetricsCollector:
    """메트릭 수집기 인스턴스 반환"""
    return metrics_collector