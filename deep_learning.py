import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt

from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import RobustScaler

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks

import warnings
warnings.filterwarnings('ignore')

def run_deep_learning_example():
    """
    아래는 실제 'DL.ipynb'에서 제공된 전체 예시 코드입니다.
    - 시계열 딥러닝 (RNN / LSTM / GRU) 비교
    - TimeSeriesSplit 교차검증, 랜덤 서치, 로그 스케일 변환 등
    - 2025년 1~2월 예측 (Recursive Multi-step 예측)
    - 모든 코드를 한 함수에 담았습니다. 실제로는 프로젝트 요구사항에 맞게 나누거나 수정하여 사용하세요.
    """

    ###############################################################################
    # 0. 라이브러리 임포트
    ###############################################################################
    import numpy as np
    import pandas as pd
    import random
    import matplotlib.pyplot as plt
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_squared_error
    from sklearn.preprocessing import RobustScaler
    import tensorflow as tf
    from tensorflow.keras import layers, models, optimizers, callbacks
    import warnings
    warnings.filterwarnings('ignore')

    print("\n=== [DL.ipynb 예시 코드 시작] ===")

    ###############################################################################
    # 1. 엑셀(다중 시트) 로딩 + 전처리
    ###############################################################################
    # 실제 사용 시 아래 파일 경로와 시트 구성을 교체하세요.
    excel_file = "(0203최종_2)상위25%_교집합_result.xlsx"
    sheets_dict = pd.read_excel(excel_file, sheet_name=None)

    # 모든 시트 열 이름 공백 제거
    for s in sheets_dict:
        sheets_dict[s].columns = sheets_dict[s].columns.str.strip()

    sheet_names = list(sheets_dict.keys())
    print("시트 목록:", sheet_names)

    ###############################################################################
    # 2. resident 시트: E열~Z열 => 2023.03 ~ 2024.12
    ###############################################################################
    months = [
        "20230331","20230430","20230531","20230630","20230731","20230831",
        "20230930","20231031","20231130","20231231","20240131","20240229",
        "20240331","20240430","20240531","20240630","20240731","20240831",
        "20240930","20241031","20241130","20241231"
    ]
    time_series_start = 4
    time_series_end   = 26

    resident_df = sheets_dict[sheet_names[0]].copy()
    cols = list(resident_df.columns)
    cols[time_series_start:time_series_end] = months
    resident_df.columns = cols

    # 22개월 승객수
    raw_passenger_counts = resident_df[months].copy()
    raw_passenger_counts = raw_passenger_counts.apply(pd.to_numeric, errors='coerce').fillna(0)
    raw_passenger_counts = raw_passenger_counts.reset_index(drop=True)

    ###############################################################################
    # 3. 부수적 시트: 평균 증가율(예시)
    ###############################################################################
    def compute_average_growth_rate(df, ts_start=4, ts_end=26):
        arr = df.iloc[:, ts_start:ts_end].apply(pd.to_numeric, errors='coerce').fillna(0).values
        eps = 1e-8
        first_val = arr[:, 0] + eps
        last_val  = arr[:, -1] + eps
        growth_rates = (last_val / first_val)**(1/(arr.shape[1]-1)) - 1.0
        return pd.Series(growth_rates)

    merged_df = resident_df.copy()
    aux_sheets = sheet_names[1:]
    for sheet in aux_sheets:
        df_sheet = sheets_dict[sheet].copy()
        merged_df[f"{sheet}_avg_growth"] = compute_average_growth_rate(
            df_sheet, time_series_start, time_series_end
        )

    ###############################################################################
    # 4. 정적 변수 / 결측치 처리 / row_index
    ###############################################################################
    static_features = [
        "O_line_count","O_exit_count","O_busstop_count",
        "D_line_count","D_exit_count","D_busstop_count"
    ]

    for c in merged_df.columns:
        merged_df[c] = pd.to_numeric(merged_df[c], errors='coerce')
        c_mean = merged_df[c].mean()
        if pd.isna(c_mean):
            c_mean = 0
        merged_df[c] = merged_df[c].fillna(c_mean)

    merged_df = merged_df.reset_index(drop=True)
    merged_df["row_index"] = merged_df.index

    # (옵션) 상위 25%만 사용 가능. 여기서는 전체 사용
    # sums = raw_passenger_counts.sum(axis=1)
    # top_n = int(len(sums)*0.25)
    # top_idx = sums.sort_values(ascending=False).index[:top_n]
    # raw_passenger_counts = raw_passenger_counts.loc[top_idx].reset_index(drop=True)
    # merged_df = merged_df.loc[top_idx].reset_index(drop=True)

    ###############################################################################
    # 5. Lag Feature(시계열 -> (batch, timesteps, features)) for RNN
    ###############################################################################
    def make_lag_features_3d(ts_array, max_lag=12):
        data_list = []
        target_list = []
        N, T = ts_array.shape
        for i in range(N):
            series = ts_array[i, :]
            for t in range(max_lag, T):
                seq = series[t-max_lag:t]
                y_val = series[t]
                data_list.append(seq.reshape(-1,1))
                target_list.append(y_val)
        X_3d = np.array(data_list)
        y_1d = np.array(target_list)
        return X_3d, y_1d

    max_lag = 12
    X_seq, y_seq = make_lag_features_3d(raw_passenger_counts.values, max_lag)
    print("X_seq.shape:", X_seq.shape)
    print("y_seq.shape:", y_seq.shape)

    ###############################################################################
    # 6. 부수적/정적 feature를 포함
    ###############################################################################
    def expand_aux_features(aux_df, max_lag=12):
        N = aux_df.shape[0]
        T = 22
        repeated_rows = []
        for i in range(N):
            row_data = aux_df.iloc[i].values
            count_for_i = (T - max_lag)
            reps = np.tile(row_data, (count_for_i, 1))
            repeated_rows.append(reps)
        return np.vstack(repeated_rows)

    aux_growth_cols = [f"{s}_avg_growth" for s in aux_sheets if f"{s}_avg_growth" in merged_df.columns]
    aux_cols = aux_growth_cols + static_features
    df_aux = merged_df[aux_cols].copy()

    static_weight = 0.01
    for sf in static_features:
        if sf in df_aux.columns:
            df_aux[sf] = df_aux[sf]*static_weight

    X_aux_2d = expand_aux_features(df_aux, max_lag=max_lag)
    print("X_aux_2d.shape:", X_aux_2d.shape)

    def combine_seq_and_aux(X_seq, X_aux_2d):
        batch_size = X_seq.shape[0]
        max_lag = X_seq.shape[1]
        K = X_aux_2d.shape[1]
        X_aux_3d = np.tile(X_aux_2d.reshape(batch_size,1,K), (1,max_lag,1))
        return np.concatenate([X_seq, X_aux_3d], axis=2)

    X_full_3d = combine_seq_and_aux(X_seq, X_aux_2d)
    print("X_full_3d.shape:", X_full_3d.shape)

    ###############################################################################
    # 7. 타깃 로그 변환 + 스케일
    ###############################################################################
    y_log = np.log1p(y_seq)
    scaler_y = RobustScaler()
    y_scaled = scaler_y.fit_transform(y_log.reshape(-1,1)).ravel()

    y_original_all = np.expm1(scaler_y.inverse_transform(y_scaled.reshape(-1,1))).ravel()
    global_y_max = y_original_all.max()

    ###############################################################################
    # 8. RNN, LSTM, GRU 세 가지 모델 중 하나 선택 (TimeSeriesSplit = 2)
    ###############################################################################
    tscv = TimeSeriesSplit(n_splits=2)
    n_iter = 2

    param_grids = {
        "RNN": {
            "units": [16, 32],
            "learning_rate": [0.01],
            "epochs": [10, 20],
            "batch_size": [16],
            "dropout": [0.0, 0.2]
        },
        "LSTM": {
            "units": [16, 32],
            "learning_rate": [0.01],
            "epochs": [10, 20],
            "batch_size": [16],
            "dropout": [0.0, 0.2]
        },
        "GRU": {
            "units": [16, 32],
            "learning_rate": [0.01],
            "epochs": [10, 20],
            "batch_size": [16],
            "dropout": [0.0, 0.2]
        }
    }

    ###############################################################################
    # 9. 모델 생성 함수 + EarlyStopping 콜백
    ###############################################################################
    def build_rnn_model(cell_type="RNN", input_shape=(12,1),
                        units=16, dropout=0.0, learning_rate=0.01):
        model = models.Sequential()
        if cell_type == "RNN":
            model.add(layers.SimpleRNN(units, input_shape=input_shape, dropout=dropout))
        elif cell_type == "LSTM":
            model.add(layers.LSTM(units, input_shape=input_shape, dropout=dropout))
        elif cell_type == "GRU":
            model.add(layers.GRU(units, input_shape=input_shape, dropout=dropout))
        model.add(layers.Dense(1))
        opt = optimizers.Adam(learning_rate=learning_rate)
        model.compile(loss="mse", optimizer=opt)
        return model

    early_stop = callbacks.EarlyStopping(
        monitor='loss', patience=3, restore_best_weights=True, verbose=0
    )

    ###############################################################################
    # 10. 교차검증 (페널티: 상수 예측/극단 예측 배제)
    ###############################################################################
    def evaluate_deep_model(cell_type, params):
        cv_scores = []
        for tr_idx, val_idx in tscv.split(X_full_3d):
            X_tr, X_val = X_full_3d[tr_idx], X_full_3d[val_idx]
            y_tr, y_val = y_scaled[tr_idx], y_scaled[val_idx]

            input_shape = (X_tr.shape[1], X_tr.shape[2])
            model_ = build_rnn_model(
                cell_type=cell_type,
                input_shape=input_shape,
                units=params["units"],
                dropout=params["dropout"],
                learning_rate=params["learning_rate"]
            )
            model_.fit(
                X_tr, y_tr, epochs=params["epochs"], batch_size=params["batch_size"],
                verbose=0, callbacks=[early_stop]
            )
            preds_scaled = model_.predict(X_val).ravel()

            if np.std(preds_scaled) < 1e-6:
                cv_scores.append(1e10)
                continue

            cv_loss = mean_squared_error(y_val, preds_scaled)

            preds_inv_log = scaler_y.inverse_transform(preds_scaled.reshape(-1,1))
            preds_val = np.expm1(preds_inv_log).ravel()
            if preds_val.max() > 3.0*global_y_max:
                cv_loss *= 10

            cv_scores.append(cv_loss)
        return np.mean(cv_scores)

    ###############################################################################
    # 11. RNN/LSTM/GRU 순회 + 랜덤 서치
    ###############################################################################
    model_results = {}
    for cell_type, grid in param_grids.items():
        print(f"\n===== 모델: {cell_type} =====")
        best_cv = np.inf
        best_par = None
        for i in range(n_iter):
            params = {
                "units": random.choice(grid["units"]),
                "learning_rate": random.choice(grid["learning_rate"]),
                "epochs": random.choice(grid["epochs"]),
                "batch_size": random.choice(grid["batch_size"]),
                "dropout": random.choice(grid["dropout"])
            }
            score = evaluate_deep_model(cell_type, params)
            print(f"[Iteration {i+1}] params={params}, CV MSE={score:.6f}")
            if score < best_cv:
                best_cv = score
                best_par = params
        model_results[cell_type] = {"best_cv": best_cv, "best_par": best_par}
        print(f" => [Best] {cell_type}, CV={best_cv:.6f}, par={best_par}")

    ###############################################################################
    # 12. 최적 모델 선정 + 전체 데이터 재학습
    ###############################################################################
    sorted_models = sorted(model_results.items(), key=lambda x: x[1]["best_cv"])
    best_model_type = sorted_models[0][0]
    best_info      = sorted_models[0][1]
    best_params    = best_info["best_par"]
    print(f"\n[최종 선택] {best_model_type}, CV={best_info['best_cv']:.6f}, params={best_params}")

    final_input_shape = (X_full_3d.shape[1], X_full_3d.shape[2])
    final_model = build_rnn_model(
        cell_type=best_model_type,
        input_shape=final_input_shape,
        units=best_params["units"],
        dropout=best_params["dropout"],
        learning_rate=best_params["learning_rate"]
    )
    final_model.fit(
        X_full_3d, y_scaled,
        epochs=best_params["epochs"],
        batch_size=best_params["batch_size"],
        verbose=0, callbacks=[early_stop]
    )

    ###############################################################################
    # 13. Recursive Multi-step 예측 (2025년01월, 2025년02월)
    ###############################################################################
    def forecast_recursive_one_rnn(ts_vals, aux_row, model_, steps=2, max_lag=12):
        preds = []
        current_series = list(ts_vals)
        for _ in range(steps):
            seq = current_series[-max_lag:]
            seq_3d = np.array(seq).reshape(1,max_lag,1)
            K = aux_row.shape[0]
            aux_3d = np.tile(aux_row.reshape(1,1,K), (1,max_lag,1))
            X_input = np.concatenate([seq_3d, aux_3d], axis=2)
            pred_scaled = model_.predict(X_input).ravel()[0]
            pred_log = scaler_y.inverse_transform([[pred_scaled]])[0,0]
            pred_val = np.expm1(pred_log)
            current_series.append(pred_val)
            preds.append(pred_val)
        return preds

    pred_202501_all = []
    pred_202502_all = []
    N = raw_passenger_counts.shape[0]

    df_aux_reset = df_aux.reset_index(drop=True)
    for i in range(N):
        row_series = raw_passenger_counts.iloc[i].values
        aux_row = df_aux_reset.iloc[i].values
        future_vals = forecast_recursive_one_rnn(row_series, aux_row,
                                                 final_model, steps=2, max_lag=12)
        pred_202501_all.append(future_vals[0])
        pred_202502_all.append(future_vals[1])

    pred_202501_all = np.array(pred_202501_all)
    pred_202502_all = np.array(pred_202502_all)

    ###############################################################################
    # 14. 최종 결과 DataFrame에 추가 + 문자열 열 복원
    ###############################################################################
    merged_df["2025년01월예측"] = pred_202501_all
    merged_df["2025년02월예측"] = pred_202502_all

    for col in ["승차_호선","승차_역","하차_호선","하차_역"]:
        if col in sheets_dict[sheet_names[0]].columns:
            merged_df[col] = sheets_dict[sheet_names[0]][col]
        else:
            print(f"주의: '{col}' 열이 원본에 없음")

    print("\n===== 최종 예측 결과 (상위 5행) =====")
    print(merged_df.head())

    ###############################################################################
    # (추가) 학습 데이터에서 MSE 확인
    ###############################################################################
    train_preds_scaled = final_model.predict(X_full_3d).ravel()
    mse_scaled = mean_squared_error(y_scaled, train_preds_scaled)

    train_preds_log = scaler_y.inverse_transform(train_preds_scaled.reshape(-1,1))
    train_preds_val = np.expm1(train_preds_log).ravel()

    train_true_log  = scaler_y.inverse_transform(y_scaled.reshape(-1,1))
    train_true_val  = np.expm1(train_true_log).ravel()

    mse_orig = mean_squared_error(train_true_val, train_preds_val)

    print(f"\n[학습 데이터] MSE(log scale)={mse_scaled:.6f}, MSE(원 스케일)={mse_orig:.6f}")

    print("=== [DL.ipynb 예시 코드 종료] ===\n")


def build_rnn_model(cell_type="RNN", input_shape=(12,1), units=16, dropout=0.0, learning_rate=0.01):
    """
    RNN / LSTM / GRU 중 하나를 생성하는 함수 (추가로 외부에서도 사용 가능).
    """
    model = models.Sequential()
    if cell_type == "RNN":
        model.add(layers.SimpleRNN(units, input_shape=input_shape, dropout=dropout))
    elif cell_type == "LSTM":
        model.add(layers.LSTM(units, input_shape=input_shape, dropout=dropout))
    elif cell_type == "GRU":
        model.add(layers.GRU(units, input_shape=input_shape, dropout=dropout))
    model.add(layers.Dense(1))
    opt = optimizers.Adam(learning_rate=learning_rate)
    model.compile(loss="mse", optimizer=opt)
    return model

if __name__ == "__main__":
    run_deep_learning_example()
