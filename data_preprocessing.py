import pandas as pd

def weighted_average_3_files():
    """
    세 개 엑셀 파일(가중평균 계산)에 대한 전처리 및 가중평균 산출 후
    최종 결과를 엑셀 파일로 저장하는 함수.
    """
    file1 = '[0131최종]상위40퍼센트_구간정보_1번째.xlsx'
    file2 = '[0131최종]상위40퍼센트_구간정보_2번째.xlsx'
    file3 = '[0131최종]상위40퍼센트_구간정보_3번째.xlsx'

    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)
    df3 = pd.read_excel(file3)

    columns = ['start_station','end_station','lines','cumulative_passenger','climate_pass']
    df1 = df1[columns].copy()
    df2 = df2[columns].copy()
    df3 = df3[columns].copy()

    df1.rename(columns={'cumulative_passenger':'cumulative_passenger_1'}, inplace=True)
    df2.rename(columns={'cumulative_passenger':'cumulative_passenger_2'}, inplace=True)
    df3.rename(columns={'cumulative_passenger':'cumulative_passenger_3'}, inplace=True)

    merged_df = pd.merge(df1, df2, on=['start_station','end_station','lines','climate_pass'], how='outer')
    merged_df = pd.merge(merged_df, df3, on=['start_station','end_station','lines','climate_pass'], how='outer')

    merged_df[['cumulative_passenger_1','cumulative_passenger_2','cumulative_passenger_3']] = \
        merged_df[['cumulative_passenger_1','cumulative_passenger_2','cumulative_passenger_3']].fillna(0)

    merged_df['weighted_average'] = (
        5*merged_df['cumulative_passenger_1'] +
        2*merged_df['cumulative_passenger_2'] +
        2*merged_df['cumulative_passenger_3']
    )/9

    final_df = merged_df[['start_station','end_station','lines','weighted_average','climate_pass']]

    unique_combinations = pd.concat([df1, df2, df3]).drop_duplicates(subset=['start_station','end_station','lines','climate_pass'])
    num_unique = unique_combinations.shape[0]
    num_final = final_df.shape[0]

    print(f'모든 파일의 고유 조합 개수: {num_unique}')
    print(f'최종 파일의 행 수: {num_final}')
    if num_unique == num_final:
        print('검증 완료: 고유 조합의 개수와 최종 파일의 행 수가 일치합니다.')
    else:
        print('검증 실패: 고유 조합의 개수와 최종 파일의 행 수가 일치하지 않습니다.')

    final_df.to_excel('[0131최종]상위40%_3개_데이터_가중평균.xlsx', index=False)


def merge_5_features_part1():
    """
    [0203최종]merged_행정구역.xlsx 와
    거주인구.xlsx 를 병합하여 merged_final_result.xlsx 생성.
    """
    file1_path = '[0203최종]merged_행정구역.xlsx'
    file2_path = r"C:\Users\bag43\Desktop\예시 데이터셋\전처리작업용\찐찐최종\거주인구.xlsx"
    output_file_path = 'merged_final_result.xlsx'

    data1 = pd.read_excel(file1_path)
    data2 = pd.read_excel(file2_path)

    data2 = data2.rename(columns={'행정구역(시군구)별':'district'})

    o_merged = data1.merge(data2, left_on='O_district', right_on='district',
                           how='left', suffixes=('', '_출발지'))
    final_data = o_merged.merge(data2, left_on='D_district', right_on='district',
                                how='left', suffixes=('', '_도착지'))

    for col in data2.columns[1:]:
        final_data.rename(columns={col: f"출발지_{col}"}, inplace=True)
        final_data.rename(columns={f"{col}_도착지":f"도착지_{col}"}, inplace=True)

    final_data = final_data.drop(columns=['district','district_도착지'])

    final_data.to_excel(output_file_path, index=False)

    print("원본 데이터 행 개수:", data1.shape[0])
    print("최종 데이터 행 개수:", final_data.shape[0])
    print("원본 데이터 열 개수:", data1.shape[1])
    print("최종 데이터 열 개수:", final_data.shape[1])


def merge_5_features_part2():
    """
    [0203최종]merged_행정구역.xlsx 과
    (0202최종)regiondata_02021729.xlsx(여러 시트) 병합 후
    merged_final_result.xlsx 로 저장.
    """
    file1_path = '[0203최종]merged_행정구역.xlsx'
    file2_path = r"C:\Users\bag43\Desktop\자료실\자료실\외부 활동\▲동아리\DSL\2025-1\EDA\(0202최종)regiondata_02021729.xlsx"
    output_file_path = 'merged_final_result.xlsx'

    data1 = pd.read_excel(file1_path)
    excel_file = pd.ExcelFile(file2_path)
    sheet_names = excel_file.sheet_names

    merged_results = {}

    for sheet in sheet_names:
        data2 = pd.read_excel(file2_path, sheet_name=sheet)
        data2 = data2.rename(columns={'end_district':'district'})

        o_merged = data1.merge(data2, left_on='O_district', right_on='district',
                               how='left', suffixes=('', '_출발지'))
        merged = o_merged.merge(data2, left_on='D_district', right_on='district',
                                how='left', suffixes=('', '_도착지'))

        for col in data2.columns:
            if col == 'district':
                continue
            if col in merged.columns:
                merged.rename(columns={col: f"출발지_{col}"}, inplace=True)
            col_d = f"{col}_도착지"
            if col_d in merged.columns:
                merged.rename(columns={col_d: f"도착지_{col}"}, inplace=True)

        merged.drop(columns=['district','district_도착지'], inplace=True, errors='ignore')
        merged_results[sheet] = merged

    with pd.ExcelWriter(output_file_path) as writer:
        for sheet, df in merged_results.items():
            df.to_excel(writer, sheet_name=sheet, index=False)

    print("file1 원본 데이터 행 개수:", data1.shape[0])
    for sheet, df in merged_results.items():
        print(f"시트 [{sheet}] - 최종 데이터 행 개수: {df.shape[0]}")
        print(f"시트 [{sheet}] - 최종 데이터 열 개수: {df.shape[1]}")


def station_encoding_final():
    """
    역정보+역행정동정보.xlsx 의 모든 시트에서
    2024년XX월 열을 복사(_copy) 후, end_station 조건별 1/0 인코딩.
    """
    file_path = "역정보+역행정동정보.xlsx"
    output_file_path = "인코딩 완료_역정보_역행정동정보.xlsx"

    xls = pd.ExcelFile(file_path)
    sheets = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}

    date_station_map = {
        "2024-04": ["양촌","구래","마산","장기","운양","걸포북변","사우","풍무","고촌","김포공항"],
        "2024-08": ["별내별가람","오남","진접","별내","다산","장자호수공원","구리","동구릉"],
        "2024-09": ["인천공항제1터미널","인천공항제2터미널"],
        "2024-11": [
            "지축","삼송","원흥","원당","화정","대곡","백석","마두","정발산","주엽","대화",
            "한국항공대","강매","행신","능곡","대곡","곡산","백마","풍산","일산","탄현",
            "능곡","대곡","곡산","백마","풍산","일산",
            "선바위","경마공원","대공원","과천","정부과천청사"
        ]
    }

    for sheet_name, df in sheets.items():
        for col in df.columns:
            if "2024년" in col and "_copy" not in col:
                df[col + "_copy"] = df[col]

        date_columns = [col for col in df.columns if "2024년" in col and "copy" in col]

        for col in date_columns:
            year_month = col.split("_")[0].replace("년 ","-").replace("월","")

            for date, stations in date_station_map.items():
                if year_month >= date:
                    df[col] = df.apply(
                        lambda row: 1 if row.get("end_station") in stations else row[col],
                        axis=1
                    )
                else:
                    df[col] = df.apply(
                        lambda row: 0 if row.get("end_station") in stations else row[col],
                        axis=1
                    )

        for col in date_columns:
            df[col] = df.apply(
                lambda row: 1 if row.get("end_station") not in sum(date_station_map.values(), [])
                                 and row.get("climate_pass") == "O" else row[col],
                axis=1
            )
            df[col] = df.apply(
                lambda row: 0 if row.get("end_station") not in sum(date_station_map.values(), [])
                                 and row.get("climate_pass") == "X" else row[col],
                axis=1
            )

    with pd.ExcelWriter(output_file_path) as writer:
        for sheet_name, df_sheet in sheets.items():
            df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"업데이트된 파일이 저장되었습니다: {output_file_path}")


def merge_bus_stop_with_encoding():
    """
    '인코딩 완료_역정보_역행정동정보 (1).xlsx' + '버스 정류장 개수.xlsx'
    모든 시트 병합 -> '병합_결과.xlsx'
    """
    encoding_file = "인코딩 완료_역정보_역행정동정보 (1).xlsx"
    bus_stop_file = "버스 정류장 개수.xlsx"
    output_file = "병합_결과.xlsx"

    df_bus_stop = pd.read_excel(bus_stop_file)
    df_bus_stop.columns = df_bus_stop.columns.str.strip()

    sheets = pd.read_excel(encoding_file, sheet_name=None)

    with pd.ExcelWriter(output_file) as writer:
        for sheet_name, df_encoding in sheets.items():
            df_encoding.columns = df_encoding.columns.str.strip()
            merged_df = df_encoding.merge(df_bus_stop, left_on="end_station", right_on="역사명", how="left")
            merged_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"모든 시트 병합 완료! 저장된 파일: {output_file}")
    print("인코딩 완료 파일의 컬럼명:", list(df_encoding.columns))
    print("버스 정류장 개수 파일의 컬럼명:", list(df_bus_stop.columns))


if __name__ == "__main__":
    # 원하는 함수 선택하여 실행.
    weighted_average_3_files()
    merge_5_features_part1()
    merge_5_features_part2()
    station_encoding_final()
    merge_bus_stop_with_encoding()