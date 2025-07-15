"""
번역 서비스
Translation service for Korean-English enum conversions
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TranslationService:
    """한국어-영어 번역 서비스"""

    # 고용형태 번역
    EMPLOYMENT_TYPE_MAP = {
        "정규직": "regular",
        "계약직": "contract",
        "임시직": "temporary",
        "일용직": "daily",
        # 역방향
        "regular": "정규직",
        "contract": "계약직",
        "temporary": "임시직",
        "daily": "일용직",
    }

    # 작업유형 번역
    WORK_TYPE_MAP = {
        "건설": "construction",
        "전기": "electrical",
        "배관": "plumbing",
        "도장": "painting",
        "용접": "welding",
        "철근": "rebar",
        "콘크리트": "concrete",
        "조적": "masonry",
        "타일": "tiling",
        "방수": "waterproofing",
        # 역방향
        "construction": "건설",
        "electrical": "전기",
        "plumbing": "배관",
        "painting": "도장",
        "welding": "용접",
        "rebar": "철근",
        "concrete": "콘크리트",
        "masonry": "조적",
        "tiling": "타일",
        "waterproofing": "방수",
    }

    # 성별 번역
    GENDER_MAP = {
        "남성": "male",
        "여성": "female",
        # 역방향
        "male": "남성",
        "female": "여성",
    }

    # 건강상태 번역
    HEALTH_STATUS_MAP = {
        "정상": "normal",
        "주의": "caution",
        "관찰": "observation",
        "치료": "treatment",
        # 역방향
        "normal": "정상",
        "caution": "주의",
        "observation": "관찰",
        "treatment": "치료",
    }

    # 건강진단 유형 번역
    EXAM_TYPE_MAP = {
        "일반": "general",
        "특수": "special",
        "배치전": "pre_placement",
        "수시": "periodic",
        # 역방향
        "general": "일반",
        "special": "특수",
        "pre_placement": "배치전",
        "periodic": "수시",
    }

    # 측정 항목 번역
    MEASUREMENT_TYPE_MAP = {
        "소음": "noise",
        "분진": "dust",
        "화학물질": "chemical",
        "온도": "temperature",
        "습도": "humidity",
        "조도": "illumination",
        "진동": "vibration",
        # 역방향
        "noise": "소음",
        "dust": "분진",
        "chemical": "화학물질",
        "temperature": "온도",
        "humidity": "습도",
        "illumination": "조도",
        "vibration": "진동",
    }

    # 사고 유형 번역
    ACCIDENT_TYPE_MAP = {
        "추락": "fall",
        "절단": "cut",
        "화상": "burn",
        "충돌": "collision",
        "끼임": "caught",
        "감전": "electric_shock",
        "중독": "poisoning",
        # 역방향
        "fall": "추락",
        "cut": "절단",
        "burn": "화상",
        "collision": "충돌",
        "caught": "끼임",
        "electric_shock": "감전",
        "poisoning": "중독",
    }

    @classmethod
    def translate_employment_type(cls, value: str) -> str:
        """고용형태 번역"""
        return cls.EMPLOYMENT_TYPE_MAP.get(value, value)

    @classmethod
    def translate_work_type(cls, value: str) -> str:
        """작업유형 번역"""
        return cls.WORK_TYPE_MAP.get(value, value)

    @classmethod
    def translate_gender(cls, value: str) -> str:
        """성별 번역"""
        return cls.GENDER_MAP.get(value, value)

    @classmethod
    def translate_health_status(cls, value: str) -> str:
        """건강상태 번역"""
        return cls.HEALTH_STATUS_MAP.get(value, value)

    @classmethod
    def translate_exam_type(cls, value: str) -> str:
        """건강진단 유형 번역"""
        return cls.EXAM_TYPE_MAP.get(value, value)

    @classmethod
    def translate_measurement_type(cls, value: str) -> str:
        """측정 항목 번역"""
        return cls.MEASUREMENT_TYPE_MAP.get(value, value)

    @classmethod
    def translate_accident_type(cls, value: str) -> str:
        """사고 유형 번역"""
        return cls.ACCIDENT_TYPE_MAP.get(value, value)

    @classmethod
    def translate_worker_data(
        cls, data: Dict[str, Any], to_english: bool = True
    ) -> Dict[str, Any]:
        """근로자 데이터 번역"""
        if not isinstance(data, dict):
            return data

        translated_data = data.copy()

        # 번역할 필드들
        translation_fields = {
            "employment_type": cls.translate_employment_type,
            "work_type": cls.translate_work_type,
            "gender": cls.translate_gender,
            "health_status": cls.translate_health_status,
        }

        for field, translator in translation_fields.items():
            if field in translated_data and translated_data[field]:
                try:
                    translated_data[field] = translator(translated_data[field])
                    logger.debug(
                        f"번역 완료: {field} {data[field]} -> {translated_data[field]}"
                    )
                except Exception as e:
                    logger.warning(f"번역 실패: {field} {data[field]} - {e}")

        return translated_data

    @classmethod
    def get_korean_label(cls, field: str, value: str) -> str:
        """영어 값에 대응하는 한국어 라벨 반환"""
        field_maps = {
            "employment_type": cls.EMPLOYMENT_TYPE_MAP,
            "work_type": cls.WORK_TYPE_MAP,
            "gender": cls.GENDER_MAP,
            "health_status": cls.HEALTH_STATUS_MAP,
            "exam_type": cls.EXAM_TYPE_MAP,
            "measurement_type": cls.MEASUREMENT_TYPE_MAP,
            "accident_type": cls.ACCIDENT_TYPE_MAP,
        }

        if field in field_maps:
            return field_maps[field].get(value, value)

        return value

    @classmethod
    def get_field_options(cls, field: str, korean: bool = True) -> Dict[str, str]:
        """필드의 모든 옵션 반환"""
        field_maps = {
            "employment_type": cls.EMPLOYMENT_TYPE_MAP,
            "work_type": cls.WORK_TYPE_MAP,
            "gender": cls.GENDER_MAP,
            "health_status": cls.HEALTH_STATUS_MAP,
            "exam_type": cls.EXAM_TYPE_MAP,
            "measurement_type": cls.MEASUREMENT_TYPE_MAP,
            "accident_type": cls.ACCIDENT_TYPE_MAP,
        }

        if field not in field_maps:
            return {}

        full_map = field_maps[field]

        if korean:
            # 한국어 키만 반환
            return {k: v for k, v in full_map.items() if not v in full_map}
        else:
            # 영어 키만 반환
            return {k: v for k, v in full_map.items() if not k in full_map.values()}


# 싱글톤 인스턴스
translation_service = TranslationService()
