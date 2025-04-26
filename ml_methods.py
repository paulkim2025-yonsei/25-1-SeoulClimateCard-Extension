import json
import pandas as pd
import numpy as np
import random
import math
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
import re
import copy
from collections import defaultdict, deque
import heapq

from sklearn.linear_model import Ridge, Lasso, LinearRegression
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, PolynomialFeatures
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
import lightgbm as lgb
from catboost import CatBoostRegressor

import warnings
warnings.filterwarnings('ignore')

###############################################################################
# subway_lines.json 불러오기
###############################################################################
def load_subway_lines(json_path='subway_lines.json'):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

###############################################################################
# (1) 여러 머신러닝 회귀 예시
###############################################################################
def example_various_ml_models():
    """
    여러 머신러닝 회귀 모델 (Ridge, Lasso, RandomForest, XGBoost, LightGBM, CatBoost 등) 
    비교 예시 함수입니다.
    실제 데이터(X, y)를 로드한 뒤 모델을 학습·평가하는 코드를 넣어서 사용하세요.
    """
    print("예시: 여러 회귀 모델 비교 함수 (데이터 로딩 후 사용 가능).")

###############################################################################
# (2) 상위 25% 추출
###############################################################################
def extract_top_25_percent():
    """
    (0203최종_2)merged_final_result.xlsx 에서 각 시트 E열~Z열(4:26열) 합산 후
    상위 25%만 추출 -> 공통 조합 -> (0203최종_2)상위25%_교집합_result.xlsx 저장
    """
    file_path = '(0203최종_2)merged_final_result.xlsx'
    xls = pd.ExcelFile(file_path)
    filtered_data_frames = []

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        columns_to_sum = df.iloc[:, 4:26]
        df['sum_E_to_Z'] = columns_to_sum.sum(axis=1)

        threshold = df['sum_E_to_Z'].quantile(0.75)
        filtered_df = df[df['sum_E_to_Z'] >= threshold]
        filtered_data_frames.append(filtered_df)

    # 첫 시트 기준 (앞의 A,B,C,D 열) 공통
    common_keys = filtered_data_frames[0][filtered_data_frames[0].columns[:4]].copy()
    for df_part in filtered_data_frames[1:]:
        common_keys = pd.merge(common_keys, df_part[df_part.columns[:4]], how='inner')

    final_results = {}
    for i, sheet_name in enumerate(xls.sheet_names):
        df_part = filtered_data_frames[i]
        result_df = pd.merge(
            common_keys, df_part, how='inner',
            on=df_part.columns[:4].tolist()
        )
        final_results[sheet_name] = result_df

    output_file = '(0203최종_2)상위25%_교집합_result.xlsx'
    with pd.ExcelWriter(output_file) as writer:
        for sheet_name, result_df in final_results.items():
            result_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"결과가 파일 '{output_file}'에 저장되었습니다.")

###############################################################################
# (3) 그래프 관련 함수들 (기동카 미지원범위 등)
###############################################################################
def remove_line_connection(graph, line_name, station_a, station_b, direction="both"):
    """
    그래프에서 station_a ↔ station_b 구간의 line_name 노선을 제거.
    direction="both"면 양방향, "forward"면 a->b만, "reverse"면 b->a만 제거.
    """
    if direction == "both":
        if station_a in graph and station_b in graph[station_a]:
            if line_name in graph[station_a][station_b]:
                graph[station_a][station_b].remove(line_name)
                if not graph[station_a][station_b]:
                    del graph[station_a][station_b]
        if station_b in graph and station_a in graph[station_b]:
            if line_name in graph[station_b][station_a]:
                graph[station_b][station_a].remove(line_name)
                if not graph[station_b][station_a]:
                    del graph[station_b][station_a]
    elif direction == "forward":
        if station_a in graph and station_b in graph[station_a]:
            if line_name in graph[station_a][station_b]:
                graph[station_a][station_b].remove(line_name)
                if not graph[station_a][station_b]:
                    del graph[station_a][station_b]
    elif direction == "reverse":
        if station_b in graph and station_a in graph[station_b]:
            if line_name in graph[station_b][station_a]:
                graph[station_b][station_a].remove(line_name)
                if not graph[station_b][station_a]:
                    del graph[station_b][station_a]

def block_segment_in_graph(graph, line_name, start, end):
    """
    subway_lines.json에서 읽은 노선(line_name)에 대해,
    start~end 사이 구간(역들)을 모두 제거.
    """
    subway_lines = load_subway_lines()
    if line_name not in subway_lines:
        return
    stations = subway_lines[line_name]
    try:
        idx_start = stations.index(start)
        idx_end = stations.index(end)
    except ValueError:
        return
    if idx_start <= idx_end:
        segment_stations = stations[idx_start : idx_end+1]
    else:
        segment_stations = stations[idx_end : idx_start+1][::-1]

    for i in range(len(segment_stations)-1):
        sA = segment_stations[i]
        sB = segment_stations[i+1]
        remove_line_connection(graph, line_name, sA, sB, direction="both")

def build_subway_graph():
    """
    subway_lines.json 로딩 후, 역 -> {인접역: set(노선들)} 형태 그래프 구성.
    6호선 응암순환 단방향, GTX-A 서울역↔수서 미개통, 특정 removal_list 구간 제거.
    """
    subway_lines = load_subway_lines()
    graph = {}

    # 그래프 노드 생성
    for line_name, stations in subway_lines.items():
        for st in stations:
            if st not in graph:
                graph[st] = {}

    # 인접 연결(양방향)
    for line_name, stations in subway_lines.items():
        for i in range(len(stations)-1):
            A = stations[i]
            B = stations[i+1]
            if B not in graph[A]:
                graph[A][B] = set()
            graph[A][B].add(line_name)

            if A not in graph[B]:
                graph[B][A] = set()
            graph[B][A].add(line_name)

    # 6호선 응암순환 단방향
    loop_6 = [
        ("응암","역촌"), ("역촌","불광"), ("불광","독바위"),
        ("독바위","연신내"), ("연신내","구산"), ("구산","응암")
    ]
    for (fa, fb) in loop_6:
        if fb in graph and fa in graph[fb]:
            if "6호선" in graph[fb][fa]:
                graph[fb][fa].remove("6호선")
                if not graph[fb][fa]:
                    del graph[fb][fa]

    # GTX-A 서울역↔수서 미개통
    gtx_a_block_pairs = [("서울역","수서")]
    for (stA, stB) in gtx_a_block_pairs:
        if stA in graph and stB in graph[stA]:
            if "GTX-A" in graph[stA][stB]:
                graph[stA][stB].remove("GTX-A")
                if not graph[stA][stB]:
                    del graph[stA][stB]
        if stB in graph and stA in graph[stB]:
            if "GTX-A" in graph[stB][stA]:
                graph[stB][stA].remove("GTX-A")
                if not graph[stB][stA]:
                    del graph[stB][stA]

    # 특정 구간 제거
    removal_list = [
        ("6호선","구산","연신내","forward"),
        ("6호선","응암","구산","forward"),
        ("6호선","역촌","응암","forward"),
        ("6호선","불광","역촌","forward"),
        ("6호선","독바위","불광","forward"),
        ("6호선","연신내","독바위","forward"),
        ("1호선","구로","인천","both"),
        ("1호선","신창","금천구청","both"),
        ("1호선","광명","병점","both"),
        ("2호선","충정로","성수","both"),
        ("2호선","신설동","신도림","both"),
        ("5호선","하남검단산","강동","both"),
        ("1호선","연천","구일","both"),
        ("1호선","연천","구로","both"),
        ("1호선","연천","금천구청","both"),
        ("1호선","연천","병점","both"),
        ("1호선","구일","구로","both"),
        ("1호선","구일","금천구청","both"),
        ("1호선","구일","병점","both"),
        ("1호선","구로","금천구청","both"),
        ("1호선","구로","병점","both"),
        ("1호선","금천구청","병점","both")
    ]
    for (line, sta_a, sta_b, direction) in removal_list:
        remove_line_connection(graph, line, sta_a, sta_b, direction)

    return graph

def bfs_shortest_path(graph, start_station, end_station):
    """
    최단 정거장수 BFS
    """
    if start_station not in graph or end_station not in graph:
        return []
    visited = set()
    queue = deque([[start_station]])
    solutions = []
    found_distance = None

    while queue:
        path = queue.popleft()
        cur = path[-1]

        if found_distance is not None and len(path)-1 > found_distance:
            continue

        if cur == end_station:
            distance_now = len(path)-1
            if found_distance is None:
                found_distance = distance_now
            if distance_now == found_distance:
                solutions.append(path)
            continue

        if cur not in visited:
            visited.add(cur)
            for neighbor in graph[cur]:
                new_path = path + [neighbor]
                queue.append(new_path)

    if not solutions:
        return []

    min_transfer = None
    best_path = None
    for candidate in solutions:
        analysis = analyze_route(graph, candidate)
        tcount = analysis["transfer_count"]
        if min_transfer is None or tcount < min_transfer:
            min_transfer = tcount
            best_path = candidate

    return best_path

def analyze_route(graph, path):
    """
    path 내 인접역들의 노선 교집합을 추적 -> 환승 횟수, 환승역, route_info 리턴
    """
    if len(path) < 2:
        return {
            "transfer_count":0,
            "transfer_stations":[],
            "route_info":[(st,[]) for st in path]
        }
    transfer_count = 0
    transfer_stations = []
    route_info = []

    st_first = path[0]
    st_second = path[1]
    if st_second not in graph[st_first]:
        return {
            "transfer_count":99999999,
            "transfer_stations":[],
            "route_info":[]
        }
    current_lines = graph[st_first][st_second]
    route_info.append((st_first, list(current_lines)))

    for i in range(len(path)-1):
        st1 = path[i]
        st2 = path[i+1]
        if st2 not in graph[st1]:
            return {
                "transfer_count":99999999,
                "transfer_stations":[],
                "route_info":[]
            }
        lines_between = graph[st1][st2]
        common = current_lines.intersection(lines_between)
        if not common:
            transfer_count += 1
            transfer_stations.append(st1)
            current_lines = lines_between
        route_info.append((st2, list(current_lines)))

    return {
        "transfer_count":transfer_count,
        "transfer_stations":transfer_stations,
        "route_info":route_info
    }

def remove_all_gtx_a_edges(graph_origin):
    """
    복사본에서 GTX-A 간선만 제거
    """
    stations = list(graph_origin.keys())
    for sA in stations:
        neighbors = list(graph_origin[sA].keys())
        for sB in neighbors:
            lines = graph_origin[sA][sB]
            if "GTX-A" in lines:
                lines.remove("GTX-A")
                if not lines:
                    del graph_origin[sA][sB]
    return graph_origin

def attempt_direct_route_same_line(line_name, start_st, end_st):
    """
    동일 노선에서 start_st->end_st 구간 역 목록 직통 확인
    """
    subway_lines = load_subway_lines()
    if line_name not in subway_lines:
        return None
    stations = subway_lines[line_name]
    if start_st not in stations or end_st not in stations:
        return None

    idx_s = stations.index(start_st)
    idx_e = stations.index(end_st)
    if idx_s < idx_e:
        return stations[idx_s:idx_e+1]
    elif idx_s > idx_e:
        return stations[idx_e:idx_s+1][::-1]
    else:
        return [start_st]

def process_row(graph, row):
    """
    row => (승차_호선, 승차_역, 하차_호선, 하차_역) 꺼내 경로 탐색
    """
    start_line = row["승차_호선"].strip()
    start_st   = row["승차_역"].strip()
    end_line   = row["하차_호선"].strip()
    end_st     = row["하차_역"].strip()

    direct_path = None
    if start_line == end_line:
        direct_path = attempt_direct_route_same_line(start_line, start_st, end_st)
        if direct_path:
            valid = True
            for i in range(len(direct_path)-1):
                sA = direct_path[i]
                sB = direct_path[i+1]
                if sB not in graph.get(sA, {}):
                    valid = False
                    break
            if not valid:
                direct_path = None

    if direct_path and len(direct_path)>1:
        path = direct_path
    else:
        path_with_gtx = bfs_shortest_path(graph, start_st, end_st)
        if not path_with_gtx:
            return []
        analysis_with_gtx = analyze_route(graph, path_with_gtx)
        used_gtx = any(("GTX-A" in lines for _, lines in analysis_with_gtx["route_info"]))
        if used_gtx:
            graph_no_gtx = remove_all_gtx_a_edges(copy.deepcopy(graph))
            path_no_gtx = bfs_shortest_path(graph_no_gtx, start_st, end_st)
            if path_no_gtx:
                len_with = len(path_with_gtx)
                len_no = len(path_no_gtx)
                if len_with <= 0.67*len_no:
                    path = path_with_gtx
                else:
                    path = path_no_gtx
            else:
                path = path_with_gtx
        else:
            path = path_with_gtx
    return path

def filter_df_main(df_main, graph, new_segments):
    """
    df_main (CSV 등) 각 행 -> process_row -> new_segments와의 교집합 검사
    """
    results = []
    for idx, row in df_main.iterrows():
        route = process_row(graph, row)
        if not route:
            continue
        # new_segments 사용 시 교집합 로직
        # ...
    return pd.DataFrame(results)

def adjust_graph_for_openings(graph, file_date):
    """
    file_date(YYYYMMDD) 이전 개통 구간은 제거
    """
    conditions = [
        {"line":"서해선","start":"대곡","end":"소사","open_date":20230701},
        {"line":"서해선","start":"일산","end":"대곡","open_date":20230826},
        {"line":"1호선","start":"연천","end":"소요산","open_date":20231216},
        {"line":"GTX-A","start":"수서","end":"성남","open_date":20240330},
        {"line":"GTX-A","start":"구성","end":"동탄","open_date":20240330},
        {"line":"GTX-A","start":"성남","end":"구성","open_date":20240629},
        {"line":"경강선","start":"판교","end":"성남","open_date":20240330},
        {"line":"경강선","start":"성남","end":"이매","open_date":20240330},
        {"line":"8호선","start":"별내","end":"암사","open_date":20240810},
        {"line":"GTX-A","start":"운정중앙","end":"서울역","open_date":20241228}
    ]
    for cond in conditions:
        if file_date < cond["open_date"]:
            block_segment_in_graph(graph, cond["line"], cond["start"], cond["end"])
    return graph

def route_analysis_main():
    """
    CSV/Excel 파일 등에서 날짜별 CSV 읽고,
    base_graph 개통 전 구간 차단 -> 경로 분석 -> 결과
    """
    base_graph = build_subway_graph()
    csv_dir = r"C:\Users\datas\EDA\기동카월별정리"
    excel_dir = r"C:\Users\datas\EDA\상위40퍼센트"

    csv_files = glob.glob(os.path.join(csv_dir,"*.csv"))
    excel_files = glob.glob(os.path.join(excel_dir,"*.xlsx"))

    for file in csv_files:
        base_name = os.path.basename(file)
        m = re.search(r'(\d{8})', base_name)
        if m:
            file_date_str = m.group(1)
            file_date = int(file_date_str)
            graph_adjusted = adjust_graph_for_openings(copy.deepcopy(base_graph), file_date)

            df_main = pd.read_csv(file)
            results = []
            for idx, row in df_main.iterrows():
                route_path = process_row(graph_adjusted, row)
                if route_path:
                    results.append(route_path)

            print(f"[{file_date_str}] 처리 완료. 총 경로 개수: {len(results)}")

if __name__ == "__main__":
    # 원하는 함수 선택하여 실행.
    example_various_ml_models()
    extract_top_25_percent()
    route_analysis_main()
