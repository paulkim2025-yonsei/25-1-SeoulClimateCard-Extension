import pandas as pd
import numpy as np
import folium
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN, KMeans
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from geopy.distance import distance

def eda_clustering_example():
    df = pd.DataFrame({
        '승차_위도': np.random.uniform(37.4, 37.7, 100),
        '승차_경도': np.random.uniform(126.8, 127.1, 100),
        '하차_위도': np.random.uniform(37.4, 37.7, 100),
        '하차_경도': np.random.uniform(126.8, 127.1, 100)
    })

    X_scaled = StandardScaler().fit_transform(df[['하차_위도','하차_경도']])
    dbscan = DBSCAN(eps=0.01, min_samples=5)
    df['dbscan_cluster'] = dbscan.fit_predict(X_scaled)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['kmeans_cluster'] = kmeans.fit_predict(df[['하차_위도','하차_경도']])

    plt.figure(figsize=(7,5))
    plt.scatter(df['하차_경도'], df['하차_위도'], c=df['kmeans_cluster'], cmap='viridis')
    plt.title("K-Means Clustering Result")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()

    return df


def count_nearby_bus_stops(subway_file_path, bus_file_gyeonggi_path, bus_file_seoul_path):
    raw_subway_data = pd.read_csv(subway_file_path)
    bus_data_gyeonggi = pd.read_csv(bus_file_gyeonggi_path)
    bus_data_seoul = pd.read_excel(bus_file_seoul_path)

    subway_cols = ["외부코드","행정구역","위도","경도"]
    subway_data = raw_subway_data[subway_cols]

    bus_cols = ["정류장번호","도시명","위도","경도"]
    bus_data_gyeonggi = bus_data_gyeonggi[bus_cols]

    bus_cols_seoul = ["ARS_ID","Y좌표","X좌표"]
    bus_data_seoul = bus_data_seoul[bus_cols_seoul]
    bus_data_seoul.rename(columns={"Y좌표":"위도","X좌표":"경도"}, inplace=True)

    results = []
    for _, subway_row in subway_data.iterrows():
        subway_id = subway_row["외부코드"]
        subway_lat, subway_lon = subway_row["위도"], subway_row["경도"]
        region = str(subway_row["행정구역"])

        if region.startswith("서울특별시"):
            filtered_buses = bus_data_seoul
        elif region.startswith("경기도") or region.startswith("충청남도"):
            filtered_buses = bus_data_gyeonggi[bus_data_gyeonggi["도시명"] == region]
        elif region.startswith("인천광역시"):
            filtered_buses = bus_data_gyeonggi[bus_data_gyeonggi["도시명"] == "인천광역시"]
        else:
            filtered_buses = pd.DataFrame()

        count_300m = sum(
            distance((subway_lat, subway_lon),(bus_row["위도"], bus_row["경도"])).meters <= 300
            for _, bus_row in filtered_buses.iterrows()
        )
        results.append({"외부코드": subway_id, "버스 정류장 개수": count_300m})

    result_df = pd.DataFrame(results)
    final_df = subway_data.merge(result_df, on="외부코드", how="left")
    return final_df


if __name__ == "__main__":
    # 원하는 함수 선택하여 실행.
    result_eda = eda_clustering_example()
    bus_stop_count_df = count_nearby_bus_stops(
        "서울시역사마스터정보.csv",
        "수도권버스정류장.csv",
        "서울시버스정류장.xlsx"
    )
