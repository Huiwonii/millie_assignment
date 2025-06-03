# 과제: RESTful 쇼핑몰 상품 관리 API

## 목차
1. [프로젝트 소개](#프로젝트-소개)  
2. [설계 및 아키텍처 개요](#설계-및-아키텍처-개요)  
3. [폴더 구조](#폴더-구조)  
4. [API 문서](#API-문서)  


---

## 환경세팅
```shell

1. docker-compose up -d 

2. requirements.txt에 설치된 패키지 설치

3. python manage.py migrate                        # manage.py는 millie/에 있습니다.

4. python manage.py loaddata fixture_books.json    # 테스트용 리소스 db 로드
   python manage.py loaddata fixture_pricing.json

5. python manage.py runserver

```

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

```plaintext 
  millie_backend/
  ├── apps/
  │   ├── product/
  │   │   ├── application/
  │   │   │   ├── product_list_use_case.py
  │   │   │   └── product_detail_use_case.py
  │   │   │
  │   │   ├── domain/
  │   │   │   ├── entity.py
  │   │   │   ├── value_objects.py
  │   │   │   └── repository.py
  │   │   │
  │   │   ├── infrastructure/
  │   │   │   └── persistence/
  │   │   │       ├── models.py
  │   │   │       ├── mapper.py
  │   │   │       └── product_repo_impl.py
  │   │   │
  │   │   └── interface/
  │   │       ├── views/
  │   │       │     ├── product_list_views.py
  │   │       │     └── product_detail_views.py
  │   │       ├── tests/
  │   │       │     ├── test_product_list_api.py
  │   │       │     └── test_product_detail_api.py
  │   │       └── serializer.py
  │   │
  │   │
  │   │
  │   │
  │   │
  │   ├── pricing/
  │   │   ├── application/
  │   │   │   ├── services/
  │   │   │   │    ├── coupon_service.py
  │   │   │   │    └── promotion_service.py
  │   │   │   │
  │   │   │   ├── use_case/
  │   │   │   │    └── calculate_price_use_case.py
  │   │   │   │
  │   │   │   └── tests/
  │   │   │        └── test_get_price_use_case.py
  │   │   │   
  │   │   ├── domain/
  │   │   │   ├── entity/
  │   │   │   │    ├── coupon.py
  │   │   │   │    ├── promotion.py
  │   │   │   │    └── price_result.py
  │   │   │   │
  │   │   │   ├── policy/
  │   │   │   │    └── discount_policy.py
  │   │   │   │
  │   │   │   ├── repositories/
  │   │   │   │    ├── coupon_repository.py
  │   │   │   │    └── promotion_repository.py 
  │   │   │   │ 
  │   │   │   └── value_objects.py
  │   │   │   │
  │   │   ├── infrastructure/
  │   │   │   └── persistence/
  │   │   │       ├── models.py
  │   │   │       ├── mapper.py
  │   │   │       └── repository_impl/
  │   │   │             ├── coupon_repo_impl.py
  │   │   │             └── promotion_repo_impl.py
  │   │   └── interface/
  │   │           ├── views/
  │   │           │     └── coupon_apply_views.py
  │   │           ├── tests/
  │   │           │     └── test_coupon_apply_api.py
  │   │           └── serializer.py
  │   │             
  │   └── utils/
  │       ├── const.py
  │       ├── exceptions.py
  │       ├── messages.py
  │       └── response.py
  │      
  ├── config/
  │   ├── settings.py
  │   ├── urls.py
  │   ├── wsgi.py
  │   └── asgi.py
  │
  ├── docker-compose.yml
  ├── fixture_books.json
  ├── fixture_pricing.json
  ├── manage.py
  └── requirements.txt
```


## API 문서
https://documenter.getpostman.com/view/36939512/2sB2qgey99

---


## 주요 기능

### 상품 리스트 조회
1. **HTTP 요청**: [GET] /api/v1/products

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
                "author": "저자 1",
                "publisher": "출판사 1",
                "published_date": "2023-01-01",
                "price": "21000.00",
                "created_at": "2025-05-29T15:49:02Z",
                "updated_at": "2025-05-29T15:49:02Z"
            },
            {
                "code": "BOOK002",
                "name": "테스트 도서 2",
                "author": "저자 2",
                "publisher": "출판사 2",
                "published_date": "2023-02-01",
                "price": "22000.00",
                "created_at": "2025-05-29T15:49:02Z",
                "updated_at": "2025-05-29T15:49:02Z"
            },
            {
                "code": "BOOK003",
                "name": "테스트 도서 3",
                "author": "저자 3",
                "publisher": "출판사 3",
                "published_date": "2023-03-01",
                "price": "23000.00",
                "created_at": "2025-05-29T15:49:02Z",
                "updated_at": "2025-05-29T15:49:02Z"
            },
            {
                "code": "BOOK006",
                "name": "테스트 도서 6",
                "author": "저자 6",
                "publisher": "출판사 6",
                "published_date": "2023-06-01",
                "price": "26000.00",
                "created_at": "2025-05-29T15:49:02Z",
                "updated_at": "2025-05-29T15:49:02Z"
            },
            {
                "code": "BOOK009",
                "name": "테스트 도서 9",
                "author": "저자 9",
                "publisher": "출판사 9",
                "published_date": "2023-09-01",
                "price": "29000.00",
                "created_at": "2025-05-29T15:49:02Z",
                "updated_at": "2025-05-29T15:49:02Z"
            }
        ]
    }

```

### 상품 상세 페이지
1. **HTTP 요청**: [GET]/api/v1/products/{code}

2. **흐름**:
    - `ProductDetailView`(interface)에서 {code}, coupon_code를 추출하여 `ProductDetailUseCase` 호출.
    - 상품 조회: `ProductRepositoryImpl.get_product_by_code(code)` → 도메인 `ProductEntity` 반환.

3. **예시 응답**:
```json
{
    "code": 200,
    "message": "OK.",
    "data": {
        "product": {
            "code": "BOOK001",
            "name": "테스트 도서 1",
            "price": 21000,
            "status": "ACTIVE",
            "created_at": "2025-05-29T15:49:02Z",
            "updated_at": "2025-05-29T15:49:02Z",
            "detail": {
                "category": "FICTION",
                "description": "이것은 테스트 도서 1의 설명입니다.",
                "status": "VISIBLE",
                "created_at": "2025-05-29T15:49:02Z",
                "updated_at": "2025-05-29T15:49:02Z"
            },
            "feature": {
                "feature": "Feature Type 1",
                "status": "VISIBLE",
                "created_at": "2025-05-29T15:49:02Z",
                "updated_at": "2025-05-29T15:49:02Z"
            },
            "publish_info": {
                "publisher": "출판사 1",
                "published_date": "2023-01-01",
                "status": "VISIBLE",
                "created_at": "2025-05-29T15:49:02Z",
                "updated_at": "2025-05-29T15:49:02Z"
            },
            "author": {
                "author": "저자 1",
                "status": "VISIBLE",
                "created_at": "2025-05-29T15:49:02Z",
                "updated_at": "2025-05-29T15:49:02Z"
            }
        },
        "available_discount": [
            {
                "code": "COUPON01",
                "name": "테스트 쿠폰 1",
                "discount_type": "PERCENTAGE",
                "discount_value": "0.10",
                "target_type": "PRODUCT",
                "target_product_code": "BOOK001",
                "target_user_id": null,
                "minimum_purchase_amount": "0.00",
                "valid_until": "2025-12-31T23:59:59Z",
                "status": "ACTIVE",
                "created_at": "2025-05-31T15:21:46.855469Z"
            },
            {
                "code": "COUPON03",
                "name": "테스트 쿠폰 3",
                "discount_type": "PERCENTAGE",
                "discount_value": "0.20",
                "target_type": "ALL",
                "target_product_code": null,
                "target_user_id": null,
                "minimum_purchase_amount": "15000.00",
                "valid_until": "2025-12-31T23:59:59Z",
                "status": "ACTIVE",
                "created_at": "2025-05-31T15:21:46.855469Z"
            }
        ]
    }
}
```




### 상품 상세 > 쿠폰적용
1. **HTTP 요청**: [POST] api/v1/pricing/apply-coupon/{code}
 - body에 coupon_code라는 key로 적용가능한 쿠폰을 배열형태로 제공
 - (예시) 
 ```json

   "coupon_code" : ["COUPON01", "COUPON02"]

 ```

2. **흐름**:
    - `CouponApplyView`(interface)에서 {code}, coupon_code를 추출하여 `CalculatePriceUseCase` 호출.
    -  쿠폰적용 및 최종 적용 및 결과계산: `CalculatePriceUseCase` → `PromotionService` (현재 진행되는 할인에 대한 연산 및 적용) , `CouponService`(요청된 쿠폰에 대한 연산 및 적용)

3. **예시 응답**:
```json
{
    "code": 200,
    "message": "OK.",
    "data": {
        "price_result": {
            "original": "21000.00",
            "discounted": "13608.00",
            "discount_amount": "7392.00",
            "discount_types": [
                "PERCENTAGE"
            ]
        },
        "available_coupons": [
            {
                "code": "COUPON01",
                "name": "테스트 쿠폰 1",
                "discount_type": "PERCENTAGE",
                "discount_value": "0.10",
                "target_type": "PRODUCT",
                "target_product_code": "BOOK001",
                "target_user_id": null,
                "minimum_purchase_amount": "0.00",
                "valid_until": "2025-12-31T23:59:59Z",
                "status": "ACTIVE",
                "created_at": "2025-05-31T15:21:46.855469Z"
            },
            {
                "code": "COUPON03",
                "name": "테스트 쿠폰 3",
                "discount_type": "PERCENTAGE",
                "discount_value": "0.20",
                "target_type": "ALL",
                "target_product_code": null,
                "target_user_id": null,
                "minimum_purchase_amount": "15000.00",
                "valid_until": "2025-12-31T23:59:59Z",
                "status": "ACTIVE",
                "created_at": "2025-05-31T15:21:46.855469Z"
            }
        ],
        "applied_pricing_policies": [
            "테스트 쿠폰 1",
            "테스트 쿠폰 3",
            "BOOK002 전용 10% 할인!!"
        ]
    }
}
```



### 테스트 시나리오 및 결과
```plaintext

[도메인 레이어(비즈니스 로직)테스트]

test_만료된_쿠폰적용시도 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_복수쿠폰순서_반대로 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_부분리턴된쿠폰_무시 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_비활성쿠폰적용 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_사용자전용쿠폰_다른사용자 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_사용자전용쿠폰_정상유저 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_상품대상쿠폰_다른상품 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_상품대상쿠폰_정상적용 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_음수_최종가격_방어 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_전체쿠폰_여러개_적용_순서1 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_전체쿠폰_여러개_적용_순서2 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_중복쿠폰코드_전달 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_최소금액미만_쿠폰적용 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_프로모션만_빈쿠폰리스트 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_프로모션만_잘못된쿠폰코드 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_프로모션만_적용 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_프로모션없고_빈쿠폰리스트 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_프로모션없고_쿠폰만적용 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_프로모션후_복수쿠폰순서 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok
test_프로모션후_쿠폰_적용 (apps.pricing.application.tests.test_get_price_use_case.GetPriceUseCaseTest) ... ok


[인터페이스 레이어 테스트 - 상품 리스트조회]
test_empty_product_list (apps.product.interface.tests.test_product_list_api.ProductListAPITest)
데이터베이스에 ACTIVE 상태 상품이 하나도 없을 때, ... ok
test_product_list_returns_active_products (apps.product.interface.tests.test_product_list_api.ProductListAPITest)
GET /api/v1/products 호출 시, ... ok


[인터페이스 레이어 테스트 - 상품 상세조회]
test_additional_product_info_fields (apps.product.interface.tests.test_product_detail_api.ProductDetailAPITest)
응답의 product 안에 'created_at'/'updated_at'이 ISO 8601 포맷 문자열로 들어가는지 확인 ... ok
test_product_detail_inactive (apps.product.interface.tests.test_product_detail_api.ProductDetailAPITest)
INACTIVE 상태의 상품 조회 → 404 Not Found ... ok
test_product_detail_nested_relations (apps.product.interface.tests.test_product_detail_api.ProductDetailAPITest)
ACTIVE 상태의 상품 조회 시, nested한 detail/feature/publish_info/author 정보가 응답에 포함되는지 확인 ... ok
test_product_detail_not_found (apps.product.interface.tests.test_product_detail_api.ProductDetailAPITest)
존재하지 않는 상품 코드 조회 → 404 Not Found ... ok
test_product_detail_without_coupon (apps.product.interface.tests.test_product_detail_api.ProductDetailAPITest)
ACTIVE 상태의 상품 조회 시, ... ok


[인터페이스 레이어 테스트 - 쿠폰 및 할인 적용]
test_bad_request_extra_params (apps.pricing.interface.tests.test_coupon_apply_api.ApplyCouponAPITest) ... ok
test_internal_error_returns_500 (apps.pricing.interface.tests.test_coupon_apply_api.ApplyCouponAPITest)
CalculatePriceUseCase.execute()가 일반 Exception을 던지면 500을 반환해야 한다. ... ok
test_product_not_found_returns_404 (apps.pricing.interface.tests.test_coupon_apply_api.ApplyCouponAPITest)
CalculatePriceUseCase.fetch()가 NotFoundException을 던지면 404를 반환해야 한다. ... ok
test_successful_apply_returns_200 (apps.pricing.interface.tests.test_coupon_apply_api.ApplyCouponAPITest)
fetch, validate, execute가 모두 성공하면 200을 반환하고, 직렬화된 결과가 와야 한다. ... ok
test_validate_failure_returns_404 (apps.pricing.interface.tests.test_coupon_apply_api.ApplyCouponAPITest)
CalculatePriceUseCase.validate()가 NotFoundException을 던지면 404를 반환해야 한다. ... ok


```