import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

def visualize_line_width(input_excel, output_png):
    df = pd.read_excel(input_excel)
    font_path = "/root/Metro_Visualization/NanumBarunGothic.ttf"
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['axes.unicode_minus'] = False

    image_width = 2656
    image_height = 2562

    line_colors = {
        "01호선":"#0052A4","02호선":"#009D3E","03호선":"#EF7C1C","04호선":"#00A5DE",
        "05호선":"#996CAC","06호선":"#CD7C2F","07호선":"#747F00","08호선":"#E6186C",
        "09호선":"#BDB092","경의선":"#77C4A3","신분당선":"#D4003B","수인분당선":"#FABE00",
        "공항철도":"#3681B7","인천1호선":"#FFCA08","인천2호선":"#ED8B00",
        "의정부경전철":"#FDA600","용인경전철":"#6FB245","우이신설경전철":"#B7C452",
        "경춘선":"#178C72","경강선":"#003DA5","서해선":"#8FC31F","신림선":"#6789CA",
        "GTX-A":"#9A6292"
    }

    min_weight = df["avg_cum_passenger"].min()
    max_weight = df["avg_cum_passenger"].max()
    df["normalized_weight"] = (df["avg_cum_passenger"] - min_weight)/(max_weight - min_weight)

    fig, ax = plt.subplots(figsize=(15,15))
    ax.set_xlim(0, image_width)
    ax.set_ylim(image_height, 0)

    for _, row in df.iterrows():
        start_x, start_y = row["start_x"], row["start_y"]
        end_x, end_y = row["end_x"], row["end_y"]
        line_color = line_colors.get(row["line_y"], "#000000")
        weight = (row["normalized_weight"]**2)*12 + 1

        ax.plot([start_x,end_x],[start_y,end_y], color=line_color, linewidth=weight, alpha=1.0)
        ax.scatter(start_x, start_y, color=line_color, s=15, zorder=3)
        ax.scatter(end_x, end_y, color=line_color, s=15, zorder=3)

    ax.set_title("가중치 기반 경로 시각화", fontsize=16, fontproperties=font_prop)
    ax.set_xlabel("X 좌표 (픽셀)", fontsize=13, fontproperties=font_prop)
    ax.set_ylabel("Y 좌표 (픽셀)", fontsize=13, fontproperties=font_prop)

    plt.savefig(output_png, dpi=300, bbox_inches="tight", transparent=False)
    plt.show()


def visualize_whole_subway_map(coordinates_folder, output_image):
    import os
    font_path = "/root/Metro_Visualization/NanumBarunGothic.ttf"
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['axes.unicode_minus'] = False

    image_width = 2656
    image_height = 2562

    line_colors = {
        "1호선":"#0052A4","2호선":"#009D3E","3호선":"#EF7C1C","4호선":"#00A5DE",
        "5호선":"#996CAC","6호선":"#CD7C2F","7호선":"#747F00","8호선":"#E6186C",
        "9호선":"#BDB092","경의선":"#77C4A3","신분당선":"#D4003B","수인분당선":"#FABE00",
        "공항철도":"#3681B7","인천1호선":"#FFCA08","인천2호선":"#ED8B00",
        "의정부경전철":"#FDA600","용인경전철":"#6FB245","우이신설경전철":"#B7C452",
        "경춘선":"#178C72","경강선":"#003DA5","서해선":"#8FC31F","신림선":"#6789CA",
        "GTX-A":"#9A6292"
    }

    files = [f for f in os.listdir(coordinates_folder) if f.endswith(".txt")]
    grouped_stations = {}

    def sort_key(station):
        code = station["외부역코드"]
        if isinstance(code, str):
            parts = code.split('-')
            if not parts[0][0].isdigit():
                main_code = (parts[0][0], int(parts[0][1:]))
            else:
                main_code = ("", int(parts[0]))
            sub_code = int(parts[1]) if len(parts)>1 else -1
        else:
            main_code = ("", code)
            sub_code = -9
        return (main_code, sub_code)

    for file_name in files:
        line_name = file_name.replace(".txt","")
        path = os.path.join(coordinates_folder, file_name)
        with open(path, "r", encoding="utf-8") as f:
            stations = eval(f.read())
            stations_sorted = sorted(stations, key=sort_key)
            grouped_stations[line_name] = stations_sorted

    fig, ax = plt.subplots(figsize=(15,15))
    ax.set_xlim(0, image_width)
    ax.set_ylim(image_height, 0)

    displayed_coordinates = set()
    for line, stations in grouped_stations.items():
        color = line_colors.get(line, "#000000")
        for i in range(len(stations)-1):
            stA = stations[i]
            stB = stations[i+1]
            if stB["노선명"] == stA["노선명"]:
                ax.plot(
                    [stA["x좌표"], stB["x좌표"]],
                    [stA["y좌표"], stB["y좌표"]],
                    color=color, linewidth=2, alpha=0.6
                )
        for station in stations:
            coord = (station["x좌표"], station["y좌표"])
            if (coord, station["노선명"]) not in displayed_coordinates:
                ax.scatter(station["x좌표"], station["y좌표"], color=color, s=4)
                ax.text(
                    station["x좌표"]+10, station["y좌표"],
                    station["역이름"], fontsize=3, color="black", fontproperties=font_prop
                )
                displayed_coordinates.add((coord, station["노선명"]))

    ax.set_title("서울 지하철 전체 노선 시각화", fontsize=16, fontproperties=font_prop)
    ax.set_xlabel("X 좌표 (픽셀)", fontsize=13, fontproperties=font_prop)
    ax.set_ylabel("Y 좌표 (픽셀)", fontsize=13, fontproperties=font_prop)

    plt.savefig(output_image, dpi=300, bbox_inches="tight", transparent=False)
    plt.show()


if __name__ == "__main__":
    visualize_line_width("0204_40p_avg_cumulative_passenger_xy.xlsx", "line_width_output.png")
    visualize_whole_subway_map(r"C:\some\folder\coordinates", "whole_subway_map.png")
