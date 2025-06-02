# 과제: RESTful 쇼핑몰 상품 관리 API

## 목차
1. [프로젝트 소개](#프로젝트-소개)  
2. [설계 및 아키텍처 개요](#설계-및-아키텍처-개요)  
3. [폴더 구조](#폴더-구조)  
4. [레이어별 설명](#레이어별-설명)  
   - [config](#config)  
   - [apps/utils](#appsutils)  
   - [apps/product](#appsproduct)  
     - [interface](#interface)  
     - [application](#application)  
     - [domain](#domain)  
     - [infrastructure](#infrastructure)  
   - [apps/pricing](#appspricing)  
     - [interface](#interface-1)  
     - [application](#application-1)  
     - [domain](#domain-1)  
     - [infrastructure](#infrastructure-1)  
5. [주요 기능](#주요-기능)  
   - [상품 리스트 조회](#상품-리스트-조회)  
   - [상품 상세 페이지: 가격 계산 로직](#상품-상세-페이지-가격-계산-로직)  
6. [API 엔드포인트](#api-엔드포인트)  
7. [실행 및 테스트 방법](#실행-및-테스트-방법)  
8. [피드백 및 개선 사항](#피드백-및-개선-사항)  

---

## 프로젝트 소개
**프로젝트명**: RESTful 쇼핑몰 상품 관리 API  
**목표**:  
- 기본 상품 리스트 조회 기능  
- 상품 상세 페이지에서의 가격 계산 (할인율 적용 + 쿠폰 적용 → 최종 판매가 도출)  

이 프로젝트는 **Clean Architecture**와 **DDD(Domain-Driven Design)** 관점에서 설계되었습니다.  
- 도메인 모델(상품, 할인, 쿠폰 등)을 명확히 분리하고,  
- 유스케이스(Use Case)를 중심으로 비즈니스 로직을 캡슐화하며,  
- 인터페이스(Controller/Serializer)와 인프라(Persistence)를 깔끔하게 분리하여 확장성을 높이려고 노력했습니다.😀

---

## 설계 및 아키텍처 개요
1. **확장 가능성**  
   - 할인 정책(정액 할인, 정률 할인, 조건부 할인 등)을 `DiscountPolicy Strategy Pattern`으로 분리하여, 정책이 추가되거나 변경되더라도 비즈니스 코드 변경을 최소화할 수 있도록 설계했습니다. 
   - 쿠폰 정책도 `Coupon Entity` → `DiscountPolicy` 변환 로직을 통해 동적으로 적용할 수 있도록 구현했습니다.
   - 할인 정책과 쿠폰 정책이 늘어나더라도, 각 정책 로직은 apps/pricing/domain/policy 하위에 구현만 추가하면 되고, repository_impl에서 DB 모델 ↔ 도메인 매핑만 해 주면 되는 구조입니다.

쿠폰 우선순위, 복합 할인 정책 등은 DiscountPolicyStrategy 확장으로 충분히 대응 가능하도록 설계했습니다.

2. **도메인 중심 설계 (DDD)**  
   - `Product`와 `Pricing` (할인·쿠폰) 도메인을 각각 별도 컨텍스트로 분리하고, 각 도메인의 **엔티티(Entity)**, **값 객체(Value Object)**, **리포지토리 인터페이스(Repository Interface)**를 정의했습니다.  
   - 애플리케이션 계층(Use Case)에서는 도메인 객체를 직접 조작하지 않고 **리포지토리 인터페이스**를 통해 접근하여, 도메인 로직을 유지했습니다.

3. **API 응답 구조 및 버전 관리**  
   - URL 레벨에 `api/v1/`을 붙여 버전 관리를 시작했습니다.  
   - 응답 바디는 `{ code, message, data }` 형식을 통일하여, 향후 버전 업이나 정책 변경 시 클라이언트 파싱 로직을 최소화했습니다.  
   - 비즈니스 로직(가격 계산 등)이 변경되더라도, JSON 응답 필드 구조는 유지되도록 노력했습니다.

---

## 폴더 구조

millie_backend/                                 # 프로젝트 루트
├── manage.py 
├── pytest.ini
├── requirements.txt
├── docker-compose.yml
├── apps/
│ ├── utils/                                    # 공통 상수 및 유틸리티 모듈
│ │ └── const.py
│ │
│ ├── product/                                  # 상품 도메인 컨텍스트
│ │ ├── interface/                              # API 레이어 (Controller + Serializer)
│ │ │ ├── product_list_views.py
│ │ │ ├── product_detail_views.py
│ │ │ └── serializer.py
│ │ │
│ │ ├── application/                            # 유스케이스(Use Case) 계층
│ │ │ ├── product_list_use_case.py
│ │ │ ├── product_detail_use_case.py
│ │ │ └── tests/                                # 비즈니스 로직 중심 테스트 코드
│ │ │ └── test_product_detail_use_case.py
│ │ │
│ │ ├── domain/                                 # 도메인 계층 (Entity, Value Object, Repository Interface, DTO 등)
│ │ │ ├── entity.py
│ │ │ ├── value_objects.py
│ │ │ ├── dto.py
│ │ │ └── repository.py
│ │ │
│ │ └── infrastructure/                         # 인프라 계층 (DB 모델, Repository 구현, Mapper)
│ │ └── persistence/
│ │ ├── models.py
│ │ ├── mapper.py
│ │ └── repository_impl.py
│ │
│ └── pricing/                                  # 가격(할인·쿠폰) 도메인 컨텍스트
│ ├── interface/                                # API Layer (Serializer)
│ │ └── serializer.py
│ │
│ ├── application/                              # 유스케이스(서비스) 계층
│ │ ├── discount_service.py
│ │ └── coupon_service.py
│ │
│ ├── domain/                                   # 도메인 계층 (Entity, Value Object, Policy, Repository Interface 등)
│ │ ├── entity/
│ │ │ ├── coupon.py
│ │ │ └── price_result.py
│ │ ├── value_objects.py
│ │ ├── repository.py
│ │ └── policy/             # 할인 정책 인터페이스 및 구현
│ │ ├── discount_policy.py
│ │ ├── condition.py
│ │ └── conditional_policy.py
│ │
│ └── infrastructure/ # 인프라 계층 (DB 모델, Repository 구현, Mapper)
│ └── persistence/
│ ├── models.py
│ ├── mapper.py
│ └── repository_impl.py
│
├── config/ # Django 설정 및 URL 라우팅
  ├── settings.py
  ├── urls.py
  ├── wsgi.py
  └── asgi.py



## API 문서
https://documenter.getpostman.com/view/36939512/2sB2qgey99

---

## 레이어별 설명

아래는 상기 폴더 구조에서 각 레이어가 어떤 역할을 하는지 간단히 정리한 내용입니다.

### config
- **위치**: `millie_backend/millie/config/`  
- **설명**:  
  - Django 전체 애플리케이션 설정 파일.  
  - `settings.py`: 데이터베이스(MySQL), INSTALLED_APPS, 미들웨어, REST 프레임워크 설정 등.  
  - `urls.py`: 애플리케이션 전역 URL 라우팅.  
    - 현재 `"/api/v1/products"` 와 `"/api/v1/products/<code>"` 두 개의 엔드포인트를 연결.  
  - `wsgi.py` / `asgi.py`: 웹 서버(Gunicorn/uWSGI, Daphne 등)와 연동용 진입점.

### apps/utils
- **위치**: `millie_backend/apps/utils/`  
- **설명**:  
  - 전역으로 사용되는 상수(`const.py`)와 공통 유틸리티 함수들을 모아둔 곳.  
  - 예를 들어 응답 형식에서 사용하는 `CODE`, `MESSAGE`, `DATA` 등의 키 값을 정의함.

### apps/product
상품 관련 비즈니스 로직(도메인)을 총괄하는 모듈입니다.

#### interface
- **위치**: `.../apps/product/interface/`  
- **내용**:  
  - **APIView (Controller)**  
    - `ProductListView`: `/api/v1/products` (상품 목록 조회)  
    - `ProductDetailView`: `/api/v1/products/<code>` (상품 상세 + 가격 계산)  
  - **Serializer**  
    - `ProductSerializer`: 도메인 객체(`ProductEntity`)를 serialize하여 JSON 형태로 변환.  
  - **역할**:  
    - HTTP 요청을 받아 **요청 파라미터 검증** → `UseCase` 호출 → 응답 데이터 serialize → HTTP 응답 반환.

#### application
- **위치**: `.../apps/product/application/`  
- **내용**:  
  - `product_list_use_case.py`: 모든 상품을 조회하는 비즈니스 로직.  
  - `product_detail_use_case.py`: 특정 상품 코드로 상품을 조회하고, 할인/쿠폰 정책을 적용하여 최종 가격을 계산하는 로직.  
  - `tests/`: 유스케이스 중심 단위 테스트. (`test_product_detail_use_case.py` 등)  
- **역할**:  
  - 도메인 레이어(Repository Interface)만 참조하여 순수 비즈니스 로직을 수행.  
  - 검증 로직(`validate()`), 엔티티 생성/가공, 필요 시 다른 유스케이스(가격 계산) 호출 등을 담당.  
  - 외부에 드러나는 세부 인프라(ORM, DB, HTTP 등) 없이 **테스트 가능한** 순수 코드로 구현됨.

#### domain
- **위치**: `.../apps/product/domain/`  
- **내용**:  
  - `entity.py`: `Product` 도메인 엔티티 정의 (예: 코드, 이름, 가격, 상태, 상세 정보, 저자, 출판정보 등).  
  - `value_objects.py`: `ProductStatus` (예: `ACTIVE`, `INACTIVE`) 등 상품 관련 값 객체 정의.  
  - `dto.py`: 도메인 레이어 내부에서 필요 시 사용하는 데이터 전달 객체(DTO) 정의.  
  - `repository.py`: `ProductRepository` 인터페이스 정의 (메서드: `get_products()`, `get_product_by_code(code)` 등).  
- **역할**:  
  - **도메인 순수 모델**을 정의하여 비즈니스 규칙을 캡슐화.  
  - 외부 구현체(PRISMA, Django ORM, SQLAlchemy 등)에 독립적.  
  - 유스케이스에서 직접 참조하여 도메인 로직을 수행.

#### infrastructure
- **위치**: `.../apps/product/infrastructure/persistence/`  
- **내용**:  
  - **Django ORM 모델** (`models.py`): 실제 DB 스키마(테이블) 정의 (`Book`, `BookDetail`, `Author`, `PublishInfo`, `Feature` 등).  
  - **Mapper** (`mapper.py`): ORM 모델 인스턴스를 도메인 엔티티(`ProductEntity`)로 변환하는 매핑 로직.  
  - **Repository 구현체** (`repository_impl.py`): `ProductRepository` 인터페이스를 Django ORM으로 구현  
    - `get_products()`: ORM 쿼리 후, 매퍼를 통해 도메인 객체 리스트 반환  
    - `get_product_by_code(code)`: ORM으로 특정 코드 검색 → 도메인 객체 반환  
- **역할**:  
  - 도메인에서 정의된 인터페이스(`ProductRepository`)를 실제 DB와 연결하여 구현.  
  - 매퍼를 활용해 ORM 모델 ↔ 도메인 객체 간 변환을 담당함으로써, 유스케이스와 도메인을 ORM에 종속되지 않게 유지.

---

### apps/pricing
상품 가격(할인/쿠폰) 관련 비즈니스 로직을 담당하는 모듈입니다.

#### interface
- **위치**: `.../apps/pricing/interface/`  
- **내용**:  
  - `serializer.py`:  
    - `CouponSummarySerializer`: 쿠폰 도메인 엔티티 → JSON serialize  
    - `PriceResultSerializer`: 가격 계산 결과(`PriceResult` 도메인 엔티티) → JSON serialize  
- **역할**:  
  - 가격 계산용 데이터(쿠폰 목록, 할인 결과 등)를 HTTP 응답에 맞는 JSON 형태로 변환.  
  - 실제 HTTP 요청/응답 로직은 `ProductDetailView`에서 이루어지며, 이곳에서 serialize만 수행.

#### application
- **위치**: `.../apps/pricing/application/`  
- **내용**:  
  - `discount_service.py`:  
    - 할인 정책을 조회하여 적용하는 비즈니스 로직.  
    - `get_discount_policies(...)`를 통해 **적용 가능한 할인 전략** 리스트를 조회 후, 최적 전략을 선택해 적용.  
  - `coupon_service.py`:  
    - 입력된 쿠폰 코드 리스트를 받아 유효한 쿠폰 도메인 객체(`CouponDomainEntity`) 반환.  
    - 쿠폰 사용 가능 여부(`is_available`) 검증 후, 최종적으로 사용할 쿠폰을 결정.  
- **역할**:  
  - 도메인 레이어(`DiscountPolicyRepository`, `CouponRepository`)를 통해 **원천 데이터**(DB의 정책/쿠폰 테이블) 조회  
  - 조회한 할인/쿠폰 정보를 기반으로 **할인 로직**을 실행  
  - 반환된 도메인 객체를 제품 상세 유스케이스에 전달

#### domain
- **위치**: `.../apps/pricing/domain/`  
- **내용**:  
  1. **엔티티(Entity)**  
     - `Coupon` (`coupon.py`): 쿠폰 고유 속성(code, valid_until, discount 정책 변환 메서드 등)  
     - `PriceResult` (`price_result.py`): 가격 계산 결과(원가(original), 할인 가격(discounted), 할인 금액(discount_amount), 할인 타입 등)  
  2. **값 객체(Value Object)**  
     - `DiscountType` (정액, 정률 구분)  
  3. **리포지토리 인터페이스(Repository Interface)**  
     - `DiscountPolicyRepository`: `get_discount_policies(target_product_code, target_user_id)`, `get_coupons_by_code(codes)` 등  
     - `CouponRepository`(alias로 겹쳐 사용)  
  4. **정책(Policy)**  
     - `DiscountPolicy` 추상 클래스 (인터페이스 역할)  
     - `PercentageDiscountPolicy`, `FixedDiscountPolicy` 등 구체 클래스  
     - `Condition`, `ConditionalPolicy` 등 필요 시 추가 로직을 수행할 수 있는 설계  
- **역할**:  
  - **가격 관련 핵심 규칙**(할인율 계산, 정액 할인 적용 등)을 순수 비즈니스 코드로 캡슐화  
  - 애플리케이션 서비스(`discount_service`, `coupon_service`)는 오직 이 인터페이스만 참조 → 구현체 독립성 확보

#### infrastructure
- **위치**: `.../apps/pricing/infrastructure/persistence/`  
- **내용**:  
  - **Django ORM 모델** (`models.py`):  
    - `DiscountPolicyModel`: 할인 정책 테이블  
    - `CouponModel`: 쿠폰 테이블  
  - **Mapper** (`mapper.py`):  
    - ORM 모델 인스턴스 → 도메인 엔티티 (`Coupon`, `DiscountPolicyStrategy`) 변환 로직  
  - **Repository 구현체** (`repository_impl.py`):  
    - `DiscountPolicyRepoImpl`: `DiscountPolicyRepository` 인터페이스를 Django ORM 기반으로 구현  
      - `get_discount_policies(...)`: 현재 유효한 정책들을 조회 후, `PercentageDiscountPolicy` 또는 `FixedDiscountPolicy` 인스턴스로 변환하여 반환  
      - `get_coupons_by_code(...)`: 쿠폰 코드 목록 조회 후, 유효 기간(`valid_until`) 체크하여 도메인 객체 리스트 반환  
- **역할**:  
  - 도메인 레이어가 정의한 **인터페이스**를 실제 DB 쿼리로 연결  
  - 정책이나 쿠폰 정보가 바뀌어도, 매퍼만 수정하면 도메인 로직은 그대로 재사용 가능



---


## 주요 기능

### 상품 리스트 조회
1. **HTTP 요청**: GET /api/v1/products

2. **흐름**:  
  - `ProductListView`(interface)에서 요청을 받는다.  
  - `ProductListUseCase`(application)을 호출하여 `ProductRepositoryImpl`에서 DB 조회 → 도메인 엔티티 리스트 반환  
  - `ProductSerializer`로 serialize 후, JSON 응답 `{ code:200, message:"OK", data:[{...}, {...}, ...] }` 반환  

3. **예시 응답**:
```json
    {
    "code": 200,
    "message": "OK.",
    "data": [
        {
        "code": "BOOK001",
        "name": "테스트 도서 1",
        "price": 22000.00,
        "status": "ACTIVE",
        "author": "한희원1",
        "publisher": "자바 출판사",
        "features": ["베스트셀러", "재고 있음"]
        },
        {
        "code": "BOOK002",
        "name": "테스트 도서 2",
        "price": 18000.00,
        "status": "ACTIVE",
        "author": "한희원2",
        "publisher": "파이썬 출판사",
        "features": ["할인 중", "주문 제작 가능"]
        }
    ]
    }
```

### 상품 상세 페이지: 가격 계산 로직
1. **HTTP 요청**: /api/v1/products/{code}?coupon_code=COUPON01&coupon_code=COUPON03

2. **흐름**:  
 - `ProductDetailView`(interface)에서 {code}, coupon_code를 추출하여 `ProductDetailUseCase` 호출.
 - 상품 조회: `ProductRepositoryImpl.get_product_by_code(code)` → 도메인 `ProductEntity` 반환.
 - 할인:
  - `DiscountService.apply_policy(user, product_code, base_price)` 호출
  - `DiscountPolicyRepoImpl.get_discount_policies(...)` → 도메인 `DiscountPolicyStrategy 리스트` 반환
 - 전략을 골라 apply()
 - 쿠폰 적용:
  - `CouponService.get_coupons_by_code([“COUPON01”, “COUPON05”])` → 도메인 `CouponDomainEntity 리스트` 반환
  - 각 쿠폰마다 is_available(user, product_code) 확인
  - `CouponDomainEntity.to_discount_policy()` 로 `DiscountPolicyStrategy` 생성 후, 현재 할인 가격에 apply()
 - 최종 PriceResult 계산 후 응답 serialize


3. **예시 응답**:
```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "product": { /* serialize 상품 정보 */ },
    "available_discounts": [ /* 사용 가능한 쿠폰 요약 정보 리스트 */ ],
    "price_result": { /* 가격 계산 결과 */ }
  }
}



