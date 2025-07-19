import os
import pandas as pd
import json
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse

def home(request):
    try:
        path_limpio = os.path.join(settings.BASE_DIR, 'sensores_app', 'sensores2_limpio.csv')
        path_anomalias = os.path.join(settings.BASE_DIR, 'sensores_app', 'anomalias.csv')

        df = pd.read_csv(path_limpio)
        df_anom = pd.read_csv(path_anomalias)

        # Crear columna fecha_hora solo para uso interno
        df['fecha_hora'] = pd.to_datetime(df['fecha'].astype(str) + ' ' + df['hora'].astype(str), errors='coerce')
        df_anom['fecha_hora'] = pd.to_datetime(df_anom['fecha'].astype(str) + ' ' + df_anom['hora'].astype(str), errors='coerce')

        # Extraer mes para agrupación
        df['mes'] = df['fecha_hora'].dt.to_period('M').astype(str)

        SENSORES = ['alcaldia', 'cabildo', 'hospital', 'juan23', 'juancojo',
                    'mangarriba', 'paraiso', 'portachuelo', 'sanandres',
                    'sandiego', 'sanesteban', 'sos', 'totumo']
        df['promedio_sensores'] = df[SENSORES].mean(axis=1)

        # Merge para traer anomaly
        df = df.merge(df_anom[['fecha_hora', 'anomaly']], on='fecha_hora', how='left')
        df['anomaly'] = df['anomaly'].fillna(0)

        # Ya no necesitamos fecha_hora en df
        df.drop(columns=['fecha_hora'], inplace=True)

        promedio_mensual = df.groupby('mes')['promedio_sensores'].mean()
        promedio_mensual_anom = df[df['anomaly'] == 1].groupby('mes')['promedio_sensores'].mean()
        promedio_mensual_anom = promedio_mensual_anom.reindex(promedio_mensual.index, fill_value=0)

        grafica_json = {
            "labels": promedio_mensual.index.tolist(),
            "datasets": [
                {
                    "label": "Promedio General",
                    "data": promedio_mensual.values.tolist(),
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "fill": False,
                    "tension": 0.3
                },
                {
                    "label": "Promedio Anomalías",
                    "data": promedio_mensual_anom.values.tolist(),
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "fill": False,
                    "tension": 0.3
                }
            ]
        }

        context = {
            'grafica_json': json.dumps(grafica_json),
            'total_lecturas': len(df),
            'total_anomalias': int(df['anomaly'].sum()),
            'error_msgs': []
        }

    except Exception as e:
        context = {
            'grafica_json': '{}',
            'total_lecturas': 0,
            'total_anomalias': 0,
            'error_msgs': [str(e)]
        }
        prediccion_resultado = None
        if request.method == "POST":
            fecha_usuario = request.POST.get('fecha_prediccion')
            if fecha_usuario:
                prediccion_resultado = predecir_pm25_para_fecha(df.copy(), SENSORES, fecha_usuario)
        context['prediccion_resultado'] = prediccion_resultado
        context['fecha_usuario'] = fecha_usuario


    return render(request, 'sensores_app/home.html', context)


def anomalias(request):
    try:
        path_anomalias = os.path.join(settings.BASE_DIR, 'sensores_app', 'anomalias.csv')
        df_anom = pd.read_csv(path_anomalias)

        if 'anomaly' not in df_anom.columns:
            raise ValueError("El archivo no contiene la columna 'anomaly'.")

        # Convertir anomaly a booleano para filtrar
        df_anom['anomaly'] = df_anom['anomaly'].astype(str).str.lower().isin(['true', '1'])
        anomalias_detectadas = df_anom[df_anom['anomaly'] == True]

        # No cargar fecha_hora, solo columnas seleccionadas
        columnas_mostrar = ['fecha', 'hora', 'promediohora']
        # Añadimos mes si existe en el dataframe
        if 'mes' in anomalias_detectadas.columns:
            columnas_mostrar.append('mes')

        tabla_html = anomalias_detectadas[columnas_mostrar].to_html(
            classes='table table-striped',
            index=False,
            table_id='tabla-anomalias'  # Para DataTables
        )

        context = {
            'tabla_anomalias': tabla_html,
            'total_anomalias': len(anomalias_detectadas),
            'error_msgs': []
        }

    except Exception as e:
        context = {
            'tabla_anomalias': '',
            'total_anomalias': 0,
            'error_msgs': [str(e)]
        }

    return render(request, 'sensores_app/anomalias.html', context)


import os
import pandas as pd
from django.conf import settings
from django.http import JsonResponse

def anomalias_data_json(request):
    try:
        path_anomalias = os.path.join(settings.BASE_DIR, 'sensores_app', 'anomalias.csv')
        df_anom = pd.read_csv(path_anomalias)

        # Convertir columna 'anomaly' a booleano
        df_anom['anomaly'] = df_anom['anomaly'].astype(str).str.lower().isin(['true', '1'])

        # Crear columna 'fecha_hora' combinando fecha y hora, parseando con pandas
        df_anom['fecha_hora'] = pd.to_datetime(df_anom['fecha'] + ' ' + df_anom['hora'], errors='coerce')

        # Filtrar solo anomalías
        anomalias_detectadas = df_anom[df_anom['anomaly'] == True]

        # Convertir fecha_hora a string ISO 'YYYY-MM-DD HH:mm' para JS
        fechas = anomalias_detectadas['fecha_hora'].dt.strftime('%Y-%m-%d %H:%M').tolist()
        valores = anomalias_detectadas['promediohora'].round(2).tolist()

        data = {
            'fechas': fechas,
            'valores': valores,
        }
    except Exception as e:
        data = {
            'error': str(e),
            'fechas': [],
            'valores': [],
        }

    return JsonResponse(data)

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np

def predecir_pm25_para_fecha(df, SENSORES, fecha_str):
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split

    df['fecha_hora'] = pd.to_datetime(df['fecha'].astype(str) + ' ' + df['hora'].astype(str), errors='coerce')
    df['hora_num'] = df['fecha_hora'].dt.hour
    df['promedio_general'] = df[SENSORES].mean(axis=1)

    for col in SENSORES:
        df.loc[df[col] > 1000, col] = df.loc[df[col] > 1000, col] / 1000
        df.loc[df[col] < 0, col] = None
        df.loc[df[col] > 100, col] = None

    df = df.dropna(subset=SENSORES)

    df['anio'] = df['fecha_hora'].dt.year
    df['mes_num'] = df['fecha_hora'].dt.month
    df['dia'] = df['fecha_hora'].dt.day
    df['dia_semana'] = df['fecha_hora'].dt.dayofweek

    df_model = df[['anio', 'mes_num', 'dia', 'dia_semana', 'promedio_general']].dropna()

    X = df_model[['anio', 'mes_num', 'dia', 'dia_semana']]
    y = df_model['promedio_general']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    modelo = RandomForestRegressor(random_state=42, n_estimators=100)
    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)

    # MAPE general
    mape_general = (abs(y_test - y_pred) / y_test).replace([float('inf'), -float('inf')], np.nan).dropna().mean() * 100

    # Predicción para la fecha solicitada
    fecha = pd.to_datetime(fecha_str)
    entrada = pd.DataFrame({
        'anio': [fecha.year],
        'mes_num': [fecha.month],
        'dia': [fecha.day],
        'dia_semana': [fecha.dayofweek]
    })

    prediccion = modelo.predict(entrada)[0]

    # Filtrar test para fecha específica
    X_test_fecha = X_test[
        (X_test['anio'] == fecha.year) &
        (X_test['mes_num'] == fecha.month) &
        (X_test['dia'] == fecha.day)
    ]

    if not X_test_fecha.empty:
        indices_fecha = X_test_fecha.index
        y_test_fecha = y_test.loc[indices_fecha]
        y_pred_fecha = y_pred[indices_fecha]

        mape_fecha = (abs(y_test_fecha - y_pred_fecha) / y_test_fecha).replace([float('inf'), -float('inf')], np.nan).dropna().mean() * 100
        mape_fecha = round(mape_fecha, 2)
    else:
        # No hay datos para esa fecha, usar MAPE general
        mape_fecha = round(mape_general, 2)

    return round(prediccion, 2), mape_fecha

    
def prediccion(request):
    prediccion_resultado = None
    porcentaje_error = None
    error_msgs = []
    fecha_usuario = None

    try:
        path_limpio = os.path.join(settings.BASE_DIR, 'sensores_app', 'sensores2_limpio.csv')
        df = pd.read_csv(path_limpio)

        SENSORES = ['alcaldia', 'cabildo', 'hospital', 'juan23', 'juancojo',
                    'mangarriba', 'paraiso', 'portachuelo', 'sanandres',
                    'sandiego', 'sanesteban', 'sos', 'totumo']

        if request.method == "POST":
            fecha_usuario_str = request.POST.get('fecha_prediccion')
            if fecha_usuario_str:
                fecha_usuario = pd.to_datetime(fecha_usuario_str).date()
                prediccion_resultado, porcentaje_error = predecir_pm25_para_fecha(df.copy(), SENSORES, fecha_usuario_str)

    except Exception as e:
        error_msgs.append(str(e))

    return render(request, 'sensores_app/prediccion.html', {
        'prediccion_resultado': prediccion_resultado,
        'porcentaje_error': porcentaje_error,
        'fecha_usuario': fecha_usuario,
        'error_msgs': error_msgs,
    })
