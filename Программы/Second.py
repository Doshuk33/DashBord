import base64
import pandas as pd
from io import StringIO
from dash import Dash, dcc, html, Input, Output
from dash.dash_table import DataTable
import plotly.express as px

app = Dash(__name__)

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Button('Загрузить файл CSV'),
        multiple=False
    ),
    dcc.DatePickerRange(
        id='date-picker-range',
        start_date=None,
        end_date=None,
        display_format='DD/MM/YYYY'
    ),
    dcc.Dropdown(
        id='category-dropdown',
        options=[],
        multi=True,
        placeholder='Выберите категории'
    ),
    dcc.RangeSlider(
        id='sales-range-slider',
        min=0,
        max=100000,  # Установите максимальное значение в зависимости от ваших данных
        value=[0, 100000],
        marks={i: str(i) for i in range(0, 100001, 10000)}
    ),
    html.Div(id='statistics'),
    dcc.Graph(id='total-sales-bar-chart'),
    dcc.Graph(id='category-sales-pie-chart'),
    DataTable(id='sales-table', columns=[], data=[])
])

@app.callback(
    Output('category-dropdown', 'options'),
    Output('category-dropdown', 'disabled'),
    Output('date-picker-range', 'disabled'),
    Output('total-sales-bar-chart', 'figure'),
    Output('category-sales-pie-chart', 'figure'),
    Output('statistics', 'children'),
    Output('sales-table', 'columns'),
    Output('sales-table', 'data'),
    Input('upload-data', 'contents'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('category-dropdown', 'value'),
    Input('sales-range-slider', 'value')
)
def update_graphs(contents, start_date, end_date, selected_categories, sales_range):
    # Загружаем данные из загруженного файла
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(StringIO(decoded.decode('utf-8')), parse_dates=['Дата'])

        # Получаем уникальные категории
        categories = df['Категория'].unique()
        options = [{'label': category, 'value': category} for category in categories]

        # Разблокируем элементы управления после загрузки файла
        date_disabled = False
        category_disabled = False
    else:
        # Если файл не загружен, возвращаем значения по умолчанию
        return [], True, True, {}, {}, [], [], []

    # Проверка на наличие выбранных дат
    if start_date is None or end_date is None:
        filtered_data = df  # Если даты не выбраны, используем все данные
    else:
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
        hover_data=['Товар']  # Добавление информации о товаре в всплывающей подсказке
    )

    pie_fig = px.pie(
        filtered_data,
        names='Категория',
        values='Сумма (в рублях)',
        title='Доля продаж по категориям'
    )

    # Статистика
    total_sum = filtered_data['Сумма (в рублях)'].sum()
    average_sum = filtered_data['Сумма (в рублях)'].mean()

    statistics = [
        html.P(f"Общая сумма продаж: {total_sum:.2f} руб."),
        html.P(f"Средняя сумма продаж: {average_sum:.2f} руб.")
    ]

    # Подготовка данных для таблицы
    sales_table_columns = [{"name": col, "id": col} for col in filtered_data.columns]
    sales_table_data = filtered_data.to_dict('records')

    return options, category_disabled, date_disabled, bar_fig, pie_fig, statistics, sales_table_columns, sales_table_data


if __name__ == '__main__':
    app.run_server(debug=True)

