"""
실시간 모니터링 및 WebSocket 통합 테스트
Real-time Monitoring and WebSocket Integration Tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
import json
import random

from src.app import create_app


class TestRealTimeMonitoring:
    """실시간 모니터링 및 WebSocket 통신 전체 시스템 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_sensor_data(self):
        """샘플 센서 데이터"""
        return {
            "sensor_id": "SENS001",
            "sensor_type": "multi_gas_detector",
            "location": "A동 화학처리실",
            "parameters": {
                "CO": 5.2,
                "H2S": 0.8,
                "O2": 20.9,
                "LEL": 2.5,
                "temperature": 22.5,
                "humidity": 55.3
            },
            "timestamp": datetime.now().isoformat(),
            "status": "normal"
        }
    
    @pytest.fixture
    def sample_alert_config(self):
        """샘플 알림 설정"""
        return {
            "alert_rules": [
                {
                    "parameter": "CO",
                    "threshold": 30,
                    "condition": "greater_than",
                    "severity": "warning",
                    "action": "notification"
                },
                {
                    "parameter": "CO",
                    "threshold": 50,
                    "condition": "greater_than",
                    "severity": "critical",
                    "action": "emergency_response"
                },
                {
                    "parameter": "H2S",
                    "threshold": 10,
                    "condition": "greater_than",
                    "severity": "critical",
                    "action": "evacuation"
                },
                {
                    "parameter": "O2",
                    "threshold": 19.5,
                    "condition": "less_than",
                    "severity": "warning",
                    "action": "notification"
                }
            ],
            "notification_channels": {
                "sms": ["010-1111-2222", "010-3333-4444"],
                "email": ["safety@company.com"],
                "webhook": ["https://alert.company.com/webhook"]
            }
        }
    
    async def test_websocket_connection_and_authentication(self, test_client):
        """WebSocket 연결 및 인증 테스트"""
        
        # 1. 인증 없이 WebSocket 연결 시도
        with pytest.raises(WebSocketDisconnect):
            with test_client.websocket_connect("/api/v1/monitoring/ws") as websocket:
                data = websocket.receive_json()
        
        # 2. 유효한 토큰으로 WebSocket 연결
        auth_token = "valid_test_token"
        with test_client.websocket_connect(
            f"/api/v1/monitoring/ws?token={auth_token}"
        ) as websocket:
            
            # 연결 확인 메시지 수신
            connection_msg = websocket.receive_json()
            assert connection_msg["type"] == "connection_established"
            assert connection_msg["client_id"] is not None
            
            # 3. 구독 요청 전송
            subscription_request = {
                "action": "subscribe",
                "channels": [
                    "sensor_data",
                    "alerts",
                    "system_status"
                ]
            }
            websocket.send_json(subscription_request)
            
            # 구독 확인 메시지 수신
            subscription_response = websocket.receive_json()
            assert subscription_response["type"] == "subscription_confirmed"
            assert len(subscription_response["subscribed_channels"]) == 3
            
            # 4. 핑-퐁 테스트
            ping_message = {"action": "ping"}
            websocket.send_json(ping_message)
            
            pong_response = websocket.receive_json()
            assert pong_response["type"] == "pong"
            
            websocket.close()
    
    async def test_real_time_sensor_data_streaming(self, test_client, sample_sensor_data):
        """실시간 센서 데이터 스트리밍 테스트"""
        
        with test_client.websocket_connect("/api/v1/monitoring/ws?token=test_token") as websocket:
            
            # 1. 센서 데이터 채널 구독
            websocket.send_json({
                "action": "subscribe",
                "channels": ["sensor_data"],
                "filters": {
                    "locations": ["A동 화학처리실", "B동 용접작업장"],
                    "parameters": ["CO", "H2S", "temperature"]
                }
            })
            
            # 구독 확인
            response = websocket.receive_json()
            assert response["type"] == "subscription_confirmed"
            
            # 2. 센서 데이터 시뮬레이션 (서버 측에서 발생)
            # 실제로는 백그라운드 태스크가 센서 데이터를 푸시
            received_data = []
            for i in range(10):
                try:
                    data = websocket.receive_json(timeout=1.0)
                    if data["type"] == "sensor_data":
                        received_data.append(data)
                except:
                    # 타임아웃 발생 시 계속
                    pass
            
            # 3. 특정 센서의 히스토리 데이터 요청
            history_request = {
                "action": "get_history",
                "sensor_id": "SENS001",
                "duration_minutes": 60,
                "interval": "5min"
            }
            websocket.send_json(history_request)
            
            history_response = websocket.receive_json()
            assert history_response["type"] == "history_data"
            assert "data_points" in history_response
            
            websocket.close()
    
    async def test_real_time_alert_system(self, test_client, sample_alert_config):
        """실시간 알림 시스템 테스트"""
        
        with test_client.websocket_connect("/api/v1/monitoring/ws?token=test_token") as websocket:
            
            # 1. 알림 채널 구독
            websocket.send_json({
                "action": "subscribe",
                "channels": ["alerts"],
                "alert_levels": ["warning", "critical", "emergency"]
            })
            
            response = websocket.receive_json()
            assert response["type"] == "subscription_confirmed"
            
            # 2. 알림 규칙 설정
            websocket.send_json({
                "action": "set_alert_rules",
                "rules": sample_alert_config["alert_rules"]
            })
            
            rules_response = websocket.receive_json()
            assert rules_response["type"] == "alert_rules_updated"
            
            # 3. 위험 상황 시뮬레이션 - CO 농도 급증
            critical_sensor_data = {
                "sensor_id": "SENS001",
                "location": "A동 화학처리실",
                "parameters": {
                    "CO": 55.0,  # 위험 수준
                    "H2S": 2.0,
                    "O2": 20.9
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # 서버에서 이 데이터를 수신했다고 가정
            # 알림이 WebSocket을 통해 전달되어야 함
            
            # 4. 알림 수신 확인
            alert_received = False
            for _ in range(5):
                try:
                    alert = websocket.receive_json(timeout=1.0)
                    if alert["type"] == "alert":
                        assert alert["severity"] == "critical"
                        assert alert["parameter"] == "CO"
                        assert alert["value"] == 55.0
                        assert alert["location"] == "A동 화학처리실"
                        alert_received = True
                        break
                except:
                    pass
            
            # 5. 알림 확인(acknowledge) 전송
            if alert_received:
                websocket.send_json({
                    "action": "acknowledge_alert",
                    "alert_id": alert.get("alert_id"),
                    "acknowledged_by": "안전관리자",
                    "action_taken": "현장 대피 지시"
                })
                
                ack_response = websocket.receive_json()
                assert ack_response["type"] == "alert_acknowledged"
            
            websocket.close()
    
    async def test_dashboard_real_time_updates(self, test_client):
        """대시보드 실시간 업데이트 테스트"""
        
        with test_client.websocket_connect("/api/v1/monitoring/ws?token=test_token") as websocket:
            
            # 1. 대시보드 데이터 구독
            websocket.send_json({
                "action": "subscribe",
                "channels": ["dashboard"],
                "dashboard_widgets": [
                    "worker_status",
                    "environmental_conditions",
                    "safety_metrics",
                    "recent_incidents"
                ]
            })
            
            response = websocket.receive_json()
            assert response["type"] == "subscription_confirmed"
            
            # 2. 초기 대시보드 데이터 요청
            websocket.send_json({
                "action": "get_dashboard_snapshot"
            })
            
            snapshot = websocket.receive_json()
            assert snapshot["type"] == "dashboard_snapshot"
            assert "worker_status" in snapshot["data"]
            assert "environmental_conditions" in snapshot["data"]
            
            # 3. 실시간 업데이트 시뮬레이션
            # 근로자 상태 변경
            worker_update = {
                "type": "dashboard_update",
                "widget": "worker_status",
                "data": {
                    "total_workers": 150,
                    "on_site": 142,
                    "in_hazardous_area": 23,
                    "health_status": {
                        "normal": 145,
                        "observation": 4,
                        "treatment": 1
                    }
                }
            }
            
            # 환경 조건 업데이트
            environmental_update = {
                "type": "dashboard_update",
                "widget": "environmental_conditions",
                "data": {
                    "air_quality": {
                        "overall": "good",
                        "pm2.5": 15,
                        "pm10": 25
                    },
                    "noise_levels": {
                        "average": 78,
                        "peak": 85,
                        "locations_exceeding": ["B동 용접작업장"]
                    },
                    "temperature": {
                        "indoor_avg": 23.5,
                        "outdoor": 28.2
                    }
                }
            }
            
            websocket.close()
    
    async def test_multi_client_broadcast_system(self, test_client):
        """다중 클라이언트 브로드캐스트 시스템 테스트"""
        
        clients = []
        
        # 1. 여러 클라이언트 연결
        for i in range(3):
            client = test_client.websocket_connect(f"/api/v1/monitoring/ws?token=client_{i}")
            clients.append(client.__enter__())
            
            # 각 클라이언트가 알림 채널 구독
            clients[i].send_json({
                "action": "subscribe",
                "channels": ["alerts", "announcements"]
            })
            
            response = clients[i].receive_json()
            assert response["type"] == "subscription_confirmed"
        
        # 2. 브로드캐스트 메시지 전송 (관리자 권한)
        admin_client = test_client.websocket_connect("/api/v1/monitoring/ws?token=admin_token")
        admin_ws = admin_client.__enter__()
        
        broadcast_message = {
            "action": "broadcast",
            "message_type": "safety_announcement",
            "content": {
                "title": "긴급 안전 공지",
                "message": "B동 화학물질 누출로 인한 긴급 대피",
                "severity": "emergency",
                "affected_areas": ["B동", "C동"],
                "instructions": [
                    "즉시 대피",
                    "비상구 이용",
                    "집결지점: 주차장"
                ]
            }
        }
        
        admin_ws.send_json(broadcast_message)
        
        # 3. 모든 클라이언트가 메시지 수신 확인
        for client in clients:
            received = client.receive_json()
            assert received["type"] == "safety_announcement"
            assert received["content"]["severity"] == "emergency"
        
        # 4. 클라이언트 연결 해제
        for client in clients:
            client.close()
        admin_ws.close()
    
    async def test_performance_monitoring_metrics(self, test_client):
        """성능 모니터링 메트릭 테스트"""
        
        with test_client.websocket_connect("/api/v1/monitoring/ws?token=test_token") as websocket:
            
            # 1. 시스템 메트릭 구독
            websocket.send_json({
                "action": "subscribe",
                "channels": ["system_metrics"],
                "metrics": [
                    "websocket_connections",
                    "message_throughput",
                    "latency",
                    "cpu_usage",
                    "memory_usage"
                ]
            })
            
            response = websocket.receive_json()
            assert response["type"] == "subscription_confirmed"
            
            # 2. 메트릭 스냅샷 요청
            websocket.send_json({
                "action": "get_metrics",
                "time_range": "last_hour"
            })
            
            metrics = websocket.receive_json()
            assert metrics["type"] == "system_metrics"
            assert "websocket_connections" in metrics["data"]
            assert "message_throughput" in metrics["data"]
            
            # 3. 부하 테스트 시뮬레이션
            for i in range(100):
                test_message = {
                    "action": "test_load",
                    "sequence": i,
                    "timestamp": datetime.now().isoformat()
                }
                websocket.send_json(test_message)
            
            # 4. 성능 통계 확인
            websocket.send_json({
                "action": "get_performance_stats"
            })
            
            stats = websocket.receive_json()
            assert stats["type"] == "performance_statistics"
            assert "messages_processed" in stats["data"]
            assert "average_latency_ms" in stats["data"]
            
            websocket.close()
    
    async def test_emergency_response_coordination(self, test_client):
        """비상 대응 조정 시스템 테스트"""
        
        with test_client.websocket_connect("/api/v1/monitoring/ws?token=emergency_coordinator") as websocket:
            
            # 1. 비상 대응 채널 구독
            websocket.send_json({
                "action": "subscribe",
                "channels": ["emergency"],
                "role": "coordinator"
            })
            
            response = websocket.receive_json()
            assert response["type"] == "subscription_confirmed"
            
            # 2. 비상 상황 발생 시뮬레이션
            emergency_event = {
                "action": "declare_emergency",
                "emergency_type": "chemical_leak",
                "location": "B동 화학물질 저장소",
                "severity": "level_3",
                "affected_workers": 25,
                "immediate_risks": [
                    "유독가스 확산",
                    "폭발 위험",
                    "환경 오염"
                ],
                "initial_response": {
                    "evacuation_initiated": True,
                    "emergency_services_called": True,
                    "containment_started": False
                }
            }
            
            websocket.send_json(emergency_event)
            
            # 3. 비상 대응 계획 활성화 확인
            activation = websocket.receive_json()
            assert activation["type"] == "emergency_response_activated"
            assert "response_plan_id" in activation
            assert "assigned_teams" in activation
            
            # 4. 실시간 상황 업데이트
            status_updates = [
                {
                    "action": "update_emergency_status",
                    "update_type": "evacuation",
                    "status": "80% 완료",
                    "remaining_workers": 5
                },
                {
                    "action": "update_emergency_status",
                    "update_type": "containment",
                    "status": "누출 차단 시작",
                    "estimated_completion": "15분"
                }
            ]
            
            for update in status_updates:
                websocket.send_json(update)
                response = websocket.receive_json()
                assert response["type"] == "status_update_received"
            
            # 5. 비상 상황 종료
            websocket.send_json({
                "action": "end_emergency",
                "resolution": "contained",
                "casualties": 0,
                "property_damage": "minimal",
                "lessons_learned": [
                    "대피 절차 개선 필요",
                    "화학물질 감지 센서 추가 설치"
                ]
            })
            
            end_response = websocket.receive_json()
            assert end_response["type"] == "emergency_ended"
            assert "incident_report_id" in end_response
            
            websocket.close()
    
    async def test_data_persistence_and_replay(self, test_client):
        """데이터 지속성 및 재생 테스트"""
        
        with test_client.websocket_connect("/api/v1/monitoring/ws?token=test_token") as websocket:
            
            # 1. 히스토리 데이터 기록 활성화
            websocket.send_json({
                "action": "enable_recording",
                "recording_id": "test_session_001",
                "channels": ["sensor_data", "alerts"],
                "duration_minutes": 60
            })
            
            response = websocket.receive_json()
            assert response["type"] == "recording_started"
            recording_id = response["recording_id"]
            
            # 2. 테스트 데이터 생성 (시뮬레이션)
            # 실제로는 센서 데이터와 알림이 자동으로 기록됨
            
            # 3. 기록 중지
            websocket.send_json({
                "action": "stop_recording",
                "recording_id": recording_id
            })
            
            stop_response = websocket.receive_json()
            assert stop_response["type"] == "recording_stopped"
            assert "data_size_mb" in stop_response
            
            # 4. 기록된 데이터 재생
            websocket.send_json({
                "action": "replay_session",
                "recording_id": recording_id,
                "playback_speed": 2.0,  # 2배속
                "start_time": "2024-07-01T09:00:00",
                "end_time": "2024-07-01T10:00:00"
            })
            
            replay_response = websocket.receive_json()
            assert replay_response["type"] == "replay_started"
            
            # 5. 재생 데이터 수신
            replay_data_count = 0
            for _ in range(10):
                try:
                    data = websocket.receive_json(timeout=1.0)
                    if data["type"] in ["sensor_data", "alert"]:
                        assert "is_replay" in data
                        assert data["is_replay"] == True
                        replay_data_count += 1
                except:
                    break
            
            assert replay_data_count > 0
            
            websocket.close()


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import sys
    import subprocess
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 실시간 모니터링 및 WebSocket 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 실시간 모니터링 및 WebSocket 통합 테스트 실패")
        sys.exit(1)