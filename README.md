# 프로젝트 제목
기후동행카드 범위 확장 제안 - 수도권 도시철도 중심

## 프로젝트 멤버
- 12기 김건우(팀장), 12기 김은희, 13기 박시현, 13기 박세현
## 프로젝트 기간
* 25.01.07 - 25.02.04

## 프로젝트 배경
대한민국에 존재하는 교통패스의 종류는 많지만 이들의 범위는 제한적이다. 또한 범위 확장의 필요성이 꾸준히 대두되고 있다. 따라서 교통패스의 효율화 및 통일화를 고려해야 한다고 생각했고, 현재 정책을 평가하고 범위 확장을 제안해보고자 하였다.

## 사용한 데이터셋
> * 기후동행카드 지하철 O/D 데이터
> * 역별 인구&상권 데이터 (유동인구, 순유동인구, 거주인구, 의료시설수, 주택매매)
> * 수도권 도시철도 역사 정보 데이터 (위도/경도 좌표, 행정구역, 노선&출구&버스정류장 개수)
> * 기후동행카드 지원 범위

## 프로젝트 내용 
#### 데이터 수집 및 전처리
- 기후동행카드 지하철 O/D 데이터: 총 승객수 중 일반요금을 내는 승객수만 선택. 호선, 역 명칭의 변경이 반영되지 않은 부분들은 통일(EX. 뚝섬유원지->자양)
- 기후동행카드 지원 범위를 기준으로 이용 가능 여부를 라벨링
- 22개월의 O/D 데이터에서 각각 구간별 승객수를 누적한 후, 승객수 상위 40% 단일구간(한정거장 차이) 중 기후동행카드 사용이 불가능한 단일구간을 선정함. 이후 여기서 선정된 단일구간을 포함하는 원래 경로를 다시 추출함.
- 추출된 32,495개의 경로에서 출발역, 도착역의 행정구역에 따라 유동인구, 순유동인구, 거주인구, 의료시설수, 주택매매 등의 도시환경 지표를 매핑함.

#### 데이터 분석 방법
- DiD회귀분석: 개입효과(=정책효과)를 분석하는 데에 특화된 회귀 기법으로, 개입이 있는 집단과 없는 집단을 비교하여 '정책의 순수한 효과'를 분석함. 단순한 평균 차이 비교 대신, '시간'에 따른 변화량을 비교함. -> treatment X time이라는 상호작용 변수를 도입한 회귀분석 방법론.
- 가설검정: 위 방법론들을 진행하면서 정규성 검증, 피어슨/스피어맨 랭크 상관계수 측정, VIF test, OLS 및 p-value로 유의성 검증 등을 진행함.
- ML/DL: 머신러닝(5개)과 딥러닝(3개) 모델을 통해, 과거 L개월의 승객수의 값을 피쳐로 하여 현재 값을 타겟으로 예측함. 이 과정에서 도시환경 변수들을 모두 보조 피쳐로 설정하여 함께 고려함. 시계열 기반 Regression 기반 방법론을 사용하였으며, 시계열에 적합한 여러 방식을 추가적으로 적용함. 이후 예측된 승객수를 기반으로 기존 값에 대해 가중평균하여 최종적으로 해당 구간을 포함했을 때의 기후동행카드의 가격을 계산함.
- DBSCAN 클러스터링: 예측된 승객수를 기준으로, 증가하는 경로들에 대해 출발역/도착역 좌표를 기준으로 DBSCAN 클러스터링을 진행함. 클러스터를 기반으로, 개별 구간 하나하나 대신 권역에 있는 모든 구간들을 지원하거나 지원하지 않는 방식을 선택함.

## 프로젝트 결론 
- 신분당선권: 신분당선 신논현-정자, 수인분당선 미금-복정 (66,000원)
- 서부권: 1호선 온수-부평, 7호선 온수-부천종합운동장, 공항철도 김포공항-검암, 서해선 김포공항-부천종합운동장 (62,000원 유지)
- 남부권: 1호선 금천구청-금정, 4호선 금정-정부과천청사 (62,000원 유지)
- 북부권: 1호선 회룡-도봉 (62,000원 유지)

## 의의 및 한계
- 국가기관 중심의 정책 방향 제시가 아닌, 실제 사용자 수요를 기반으로 한 새로운 방향 제시
- 선행 연구는 설문조사 기반이 많았으나, 위 프로젝트는 빅데이터를 기반으로 함
- 시계열 특성을 적극적으로 활용함

- 원본 데이터가 매월 말일만 존재하였음
- 버스에 대한 분석이 부족함
- 각 지자체와 예산 등 협의해야할 부분이 여전히 다수 존재함

--------------------------------------------------
# Project Title
**Proposal for Expanding the Scope of the Climate Companion Card(기후동행카드) – Focused on Metropolitan Area Urban Rail(수도권 도시철도)**

## Project Members
- **12th Cohort** Kim Geon-woo(김건우) — *Team Leader*  
- **12th Cohort** Kim Eun-hee(김은희)  
- **13th Cohort** Park Si-hyun(박시현)  
- **13th Cohort** Park Se-hyun(박세현)  

## Project Period
*25 Jan 07 – 25 Feb 04*

## Project Background
The **Republic of Korea(대한민국)** offers many kinds of transit passes, yet their coverage is limited and the need for expansion is consistently raised.  
This project evaluates existing policies and proposes broader, more unified coverage for transportation passes.

## Datasets Used
- **Climate Companion Card Subway O/D Data(기후동행카드 지하철 O/D 데이터)**  
- **Station-level Demographic & Commercial-zone Data(역별 인구&상권 데이터)**  
  - floating population, net floating population, residential population, number of medical facilities, housing transactions  
- **Metropolitan-Area Urban-Rail Station Information Data(수도권 도시철도 역사 정보 데이터)**  
  - latitude / longitude, administrative districts, counts of lines, exits, and bus stops  
- **Current Coverage of the Climate Companion Card(기후동행카드 지원 범위)**  

## Project Details
### Data Collection & Pre-processing
1. **Climate Companion Card Subway O/D Data**  
   - Selected only passengers paying the regular fare among total riders.  
   - Unified outdated line and station names (e.g. *Ttukseom Hangang Park(뚝섬유원지)* → *Jayang(자양)*).  
2. **Labeling Availability**  
   - Labeled each section as available or unavailable according to current card coverage.  
3. **Section Extraction**  
   - Accumulated monthly passengers over **22 months**, chose adjacent-station sections in the top **40 %** ridership where the card is unusable, then re-extracted the original routes containing those sections.  
4. **Urban-Environment Mapping**  
   - For **32 495** extracted routes, mapped urban-environment indicators (floating & net floating population, residential population, medical facilities, housing transactions) using the administrative districts of origin and destination stations.

### Analytical Methods
| Method | Purpose & Notes |
|--------|-----------------|
| **Difference-in-Differences (DiD) Regression(DiD회귀분석)** | Estimates pure policy effects by comparing treated vs. untreated groups over time via a *treatment × time* interaction. |
| **Hypothesis Testing** | Normality checks, Pearson / Spearman rank correlations, VIF, OLS estimation, *p*-value significance. |
| **ML / DL Time-series Models** | Five ML and three DL models predicted current ridership from the past *L* months, with all urban-environment variables as auxiliary features. Predicted and actual ridership were combined by weighted average to compute proposed card prices per route. |
| **DBSCAN Clustering(DBSCAN 클러스터링)** | Clustered routes with increasing predicted ridership (based on origin/destination coordinates) to decide coverage by cluster rather than by individual section. |

## Project Conclusions
- **Sinbundang Corridor(신분당선권)**  
  - *Sinbundang Line(신분당선)* **Sinnonhyeon(신논현)** – **Jeongja(정자)**  
  - *Suin–Bundang Line(수인분당선)* **Migeum(미금)** – **Bokjeong(복정)**  
  - **66 000 KRW**  
- **Western Corridor(서부권)** — **62 000 KRW** (maintain)  
  - *Line 1(1호선)* **Onsu(온수)** – **Bupyeong(부평)**  
  - *Line 7(7호선)* **Onsu(온수)** – **Bucheon Sports Complex(부천종합운동장)**  
  - *Airport Railroad(공항철도)* **Gimpo Int’l Airport(김포공항)** – **Geomam(검암)**  
  - *Seohae Line(서해선)* **Gimpo Int’l Airport(김포공항)** – **Bucheon Sports Complex(부천종합운동장)**  
- **Southern Corridor(남부권)** — **62 000 KRW** (maintain)  
  - *Line 1(1호선)* **Geumcheon-gu Office(금천구청)** – **Geumjeong(금정)**  
  - *Line 4(4호선)* **Geumjeong(금정)** – **Government Complex Gwacheon(정부과천청사)**  
- **Northern Corridor(북부권)**  
  - *Line 1(1호선)* **Hoeryong(회룡)** – **Dobong(도봉)** — **62 000 KRW** (maintain)  

## Significance & Limitations
### Significance
- Provides **user-demand-driven** policy direction instead of a purely top-down national approach.  
- Leverages **big-data analysis** rather than survey-based methods of prior studies.  
- Actively exploits **time-series characteristics** in modeling.

### Limitations
- Original ridership data exist only as **end-of-month snapshots**.  
- **Bus data analysis** remains insufficient.  
- Requires extensive **coordination with local governments** and budget negotiations.  
