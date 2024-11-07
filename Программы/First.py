import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
from io import StringIO
import base64

# Создание приложения Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Анализ продаж товаров", style={'textAlign': 'center'}),
    html.Div("Загрузите CSV файл с данными о продажах:", style={'textAlign': 'center'}),

    dcc.Upload(
        id='upload-data',
        children=html.Button('Загрузить файл'),
        style={
            'width': '20%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'solid',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px auto'
        }
    ),

    dcc.DatePickerRange(
        id='date-picker-range',
        display_format='YYYY-MM-DD'
    ),

    dcc.Dropdown(
        id='category-dropdown',
        multi=True,
        placeholder="Выберите категории"
    ),

    dcc.RangeSlider(
        id='sales-range-slider',
        min=0,
        max=1000000,  # Установите максимальное значение по вашему усмотрению
        step=1000,
        value=[0, 1000000],
        marks={i: f'{i}' for i in range(0, 1000001, 100000)},
        tooltip={"placement": "bottom", "always_visible": True}
    ),

    html.Button('Сбросить фильтры', id='reset-button', n_clicks=0),

    html.Div([
        dcc.Graph(id='total-sales-bar-chart'),
        dcc.Graph(id='category-sales-pie-chart'),
    ]),

    html.Div(id='statistics', style={'margin-top': '20px'}),

    dash_table.DataTable(id='sales-table')
])


@app.callback(
    Output('category-dropdown', 'options'),
    Output('total-sales-bar-chart', 'figure'),
    Output('category-sales-pie-chart', 'figure'),
    Output('statistics', 'children'),
    Output('sales-table', 'data'),
    Input('upload-data', 'contents'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('category-dropdown', 'value'),
    Input('sales-range-slider', 'value'),
    Input('reset-button', 'n_clicks')
)
def update_graphs(contents, start_date, end_date, selected_categories, sales_range, n_clicks):
    # Загружаем данные из загруженного файла
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(StringIO(decoded.decode('utf-8')), parse_dates=['Дата'])

        # Получаем уникальные категории
        categories = df['Категория'].unique()
        options = [{'label': category, 'value': category} for category in categories]
    else:
        return [], dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Если кнопка сброса была нажата, вернуть все фильтры к начальным значениям
    if n_clicks > 0:
        return options, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Фильтрация данных на основе выбранных дат
    filtered_data = df[(df['Дата'] >= start_date) & (df['Дата'] <= end_date)]

    # Фильтрация по категориям, если выбраны
    if selected_categories:
        filtered_data = filtered_data[filtered_data['Категория'].isin(selected_categories)]

    # Фильтрация по диапазону суммы
    filtered_data = filtered_data[
        (filtered_data['Сумма (в рублях)'] >= sales_range[0]) &
        (filtered_data['Сумма (в рублях)'] <= sales_range[1])
        ]

    # Построение графиков
    bar_fig = px.bar(
        filtered_data,
        x='Дата',
        y='Сумма (в рублях)',
        title='Сумма продаж по датам',
        color='Категория',
        barmode='group',
        hover_data=['Товар']  # Добавление информации о товаре при наведении
    )

    pie_fig = px.pie(
        filtered_data,
        names='Категория',
        values='Сумма (в рублях)',
        title='Доля продаж по категориям',
        hover_data=['Сумма (в рублях)']  # Добавление информации о сумме при наведении
    )

    # Статистика
    total_sum = filtered_data['Сумма (в рублях)'].sum()
    average_sum = filtered_data['Сумма (в рублях)'].mean()

    statistics = [
        html.P(f"Общая сумма продаж: {total_sum:.2f} руб."),
        html.P(f"Средняя сумма продаж: {average_sum:.2f} руб.")
    ]

    # Данные для таблицы
    sales_table_data = filtered_data.to_dict('records')

    return options, bar_fig, pie_fig, statistics, sales_table_data


if __name__ == '__main__':
    app.run_server(debug=True)

