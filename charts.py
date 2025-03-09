import numpy as np
import re
import matplotlib.pyplot as plt
from matplotlib import cm 
from matplotlib.patches import Circle
from matplotlib.colors import LinearSegmentedColormap
# import seaborn as sns
from scipy.stats import gaussian_kde
from scipy.ndimage import gaussian_filter
import matplotlib.dates as mdates
import pandas as pd
import os
import cv2
import colorama
import datetime


class Charts:
    def __init__(self):
        # self.file_num = file_num
        # self.fixations = fixations
        # self.path1 = None
        # self.raw_data = []
        # self.df = None
        self.width = 2560
        self.height = 1440

    def log(self, message, level="INFO", source="NA"):
        """Функция для красивого вывода логов"""
        colors = {
            "INFO": colorama.Fore.CYAN,   # Голубой
            "WARNING": colorama.Fore.YELLOW,  # Желтый
            "ERROR": colorama.Fore.RED,   # Красный
            "SUCCESS": colorama.Fore.GREEN,  # Зеленый
        }
        
        now = datetime.datetime.now().strftime("%H:%M:%S")  # Получаем текущее время (часы:минуты:секунды)
        color = colors.get(level, colorama.Fore.WHITE)  # Получаем цвет (по умолчанию белый)
        
        print(f"{color}[{now}] [{level}] ({source}) {message}{colorama.Style.RESET_ALL}")
    
    def get_folder_number(self, path):
        # Используем регулярное выражение для извлечения номера после 'gazeTracktion'
        match = re.search(r'gazeTracktion(\d+)', path)
        if match:
            return int(match.group(1))  # Возвращаем номер папки как целое число
        else:
            return None  # Возвращаем None, если путь не соответствует шаблону

    def scatter_plot_pictures(self, folder_path=None, width=1920, height=1080, fixations=False, alpha_bg=0.2, alpha_gaze=0.05, title="", xlable="", ylable=""):

        """Метод для построения диаграммы рассеивания"""

        folder_number = self.get_folder_number(folder_path)
        gaze_path = folder_path + f"/gaze{folder_number}.txt"
        fixation_path = folder_path + f"/fix{folder_number}.txt"

        self.raw_data = []
        with open(gaze_path, 'r') as file:
            for line in file:
                x, y, r, timestamp, time = line.strip().split(',')
                s = min(np.pi * (int(r) ** 2), 3000)
                self.raw_data.append((int(x), int(y), int(r), int(s), int(timestamp), time))

        # Преобразование данных в DataFrame
        self.df = pd.DataFrame(self.raw_data, columns=['x', 'y', 'r', 's', 'timestamp', 'time'])

        # Извлекаем координаты точек
        x = self.df['x'].tolist()
        y = self.df['y'].tolist()
        s = self.df['s'].tolist()

        # Загрузка изображения фона
        background_image_path = folder_path + f'/image.png'
        background_image = cv2.imread(background_image_path)
        background_image = cv2.cvtColor(background_image, cv2.COLOR_BGR2RGB)
        background_image = cv2.resize(background_image, (width, height))

        # Отображение фона с точками
        plt.figure(figsize=(16, 9))
        plt.imshow(background_image, alpha=alpha_bg)  # Используем изображение в качестве фона
        plt.scatter(x, y, color='red', s=s, alpha=alpha_gaze)

        if fixations:
            try:
                # Чтение данных фиксации
                fixations_data = []
                with open(fixation_path, 'r') as file:
                    for line in file:
                        fix_x, fix_y, fix_radius, duration, dispersion, std_dev = line.strip().split(',')
                        s = min(np.pi * ((int(fix_radius) / 3) ** 2), 100000000)
                        fixations_data.append((int(fix_x), int(fix_y), float(fix_radius), int(s), float(duration), float(dispersion), float(std_dev)))

                df_fix = pd.DataFrame(fixations_data, columns=['fix_x', 'fix_y', 'fix_radius', 's', 'duration', 'dispersion', 'std_dev'])

                # Нормализация длительности
                min_duration = df_fix['duration'].min()
                max_duration = df_fix['duration'].max()
                norm_duration = (df_fix['duration'] - min_duration) / (max_duration - min_duration)

                custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", ["cyan", "darkblue"])
                colors = custom_cmap(norm_duration)

                # Отображение окружностей с градиентными цветами
                ax = plt.gca()
                for index, (fix_x, fix_y, fix_radius, color) in enumerate(zip(df_fix['fix_x'], df_fix['fix_y'], df_fix['fix_radius'], colors), start=1):
                    circle = Circle((fix_x, fix_y), fix_radius, color=color, fill=False, hatch='//', linewidth=1, alpha=0.3)
                    ax.add_patch(circle)
                    plt.text(fix_x, fix_y, str(index), fontsize=8, color='black', ha='center', va='center')

                # Градиент
                gradient = np.linspace(0, 1, 256).reshape(1, -1)
                gradient = np.vstack([gradient] * 5)
                ax.imshow(gradient, aspect='equal', cmap=custom_cmap, extent=[0.02 * width, 0.12 * width, 0.92 * height, 0.95 * height])

                # Добавление аннотаций
                plt.text(0.025 * width, 0.973 * height, f'{min_duration:.2f} с', fontsize=6, color='black', bbox=dict(facecolor='white', alpha=0.7))
                plt.text(0.115 * width, 0.973 * height, f'{max_duration:.2f} с', fontsize=6, color='black', ha='right', bbox=dict(facecolor='white', alpha=0.7))
            except Exception as e:
                self.log(f"Произошла ошибка при обработке фиксаций для построения графика: {e}", "ERROR", "charts")


        # Настройки графика
        plt.title(title)
        plt.xlabel(xlable)
        plt.ylabel(ylable)
        plt.xlim(0, width)
        plt.ylim(height, 0)
        savename = folder_path + f'/scatter_plot{folder_number}.png'
        plt.savefig(savename, dpi=300)
        self.log(f"Диаграмма рассеивания готова", "SUCCESS", "charts")
        plt.show()

    def scatter_plot_testing(self, folder_path=None, width=1920, height=1080, fixations=False):

        folder_number = self.get_folder_number(folder_path)
        gaze_path = folder_path + f"/gaze{folder_number}.txt"
        fixation_path = folder_path + f"/fix{folder_number}.txt"

        raw_data = []
        row_len = 0
        with open(gaze_path, 'r') as file:
            for line in file:
                temp = line.strip().split(',')
                row_len = len(temp)
                break
            # print(row_len)
            if row_len == 6:
                for line in file:
                    x, y, target_x, target_y, timestamp, time = line.strip().split(',')
                    raw_data.append((int(x), int(y), int(target_x), int(target_y), int(timestamp), time))
            else:
                for line in file:
                    x, y, r, target_x, target_y, timestamp, time = line.strip().split(',')
                    s = min(np.pi * (int(r) ** 2), 3000)
                    raw_data.append((int(x), int(y), int(r), int(s), int(target_x), int(target_y), int(timestamp), time))

        if row_len == 6:
            # Преобразование данных в DataFrame
            df = pd.DataFrame(raw_data, columns=['x', 'y', 'target_x', 'target_y', 'timestamp', 'time'])
            red_radius = 50  # Радиус красных кружков
        else:
            # Преобразование данных в DataFrame
            df = pd.DataFrame(raw_data, columns=['x', 'y', 'r', 's', 'target_x', 'target_y', 'timestamp', 'time'])


        # Извлекаем координаты точек и целей
        x = df['x'].tolist()
        y = df['y'].tolist()
        target_x = df['target_x'].tolist()
        target_y = df['target_y'].tolist()
        if row_len != 6:
            r = df['r'].tolist()
            s = df['s'].tolist()


        # Получаем список уникальных целей из данных тестирования
        unique_targets = list(set(zip(target_x, target_y)))

        # Создание белого фона
        img_array = np.ones((height, width, 3))

        # Отображение белого фона
        plt.figure(figsize=(16, 9))
        plt.imshow(img_array)

        # Инициализируем словарь для метрик оценивания
        target_metrics = {}

        # Цикл по уникальным целям для расчета статистики по каждой из них
        for target in unique_targets:
            target_hits = 0
            target_valid_points = 0
            target_squared_errors = []
            target_distances = []
            target_x_pos, target_y_pos = target
            target_radius = int(width * 0.0390625)
            
            # Фильтрация данных для текущей цели (оставляем только те строки, которые относятся к определенной цели)
            target_data = df[(df['target_x'] == target_x_pos) & (df['target_y'] == target_y_pos)]
            if row_len != 6:
                for i, (x_point, y_point, red_r, red_s) in target_data[['x', 'y', 'r', 's']].iterrows():
                    # Вычисление расстояния до текущей цели
                    distance = max(0, np.sqrt((x_point - target_x_pos) ** 2 + (y_point - target_y_pos) ** 2) - (red_r + target_radius))
                    min_distance = distance
                    
                    # Учитываем только точки, которые находятся в пределах разумного расстояния от цели (2 радиуса цели)
                    if min_distance <= target_radius * 2:
                        target_valid_points += 1
                        target_distances.append(min_distance)
                        # Проверка на попадание
                        if distance == 0:
                            target_hits += 1
                        # Добавление квадрата ошибки для расчета RMS
                        target_squared_errors.append(min_distance ** 2)
            else:
                for i, (x_point, y_point) in target_data[['x', 'y']].iterrows():
                    red_r = 50
                    # Вычисление расстояния до текущей цели
                    distance = max(0, np.sqrt((x_point - target_x_pos) ** 2 + (y_point - target_y_pos) ** 2) - (red_r + target_radius))
                    min_distance = distance
                    
                    # Учитываем только точки, которые находятся в пределах разумного расстояния от цели (2 радиуса цели)
                    if min_distance <= target_radius * 2:
                        target_valid_points += 1
                        target_distances.append(min_distance)
                        # Проверка на попадание
                        if distance == 0:
                            target_hits += 1
                        # Добавление квадрата ошибки для расчета RMS
                        target_squared_errors.append(min_distance ** 2)
            
            # Расчет метрик для текущей цели
            total_points = target_valid_points
            accuracy = target_hits / total_points * 100 if total_points > 0 else 0
            rms_error = np.sqrt(np.mean(target_squared_errors)) if len(target_squared_errors) > 0 else 0
            mean_distance = np.mean(target_distances) if len(target_distances) > 0 else 0
            
            # Сохранение метрик для текущей цели
            target_metrics[target] = {
                'accuracy': accuracy,
                'total_points': total_points,
                'hits': target_hits,
                'rms_error': rms_error,
                'mean_distance': mean_distance
            }
            
            # Отображение синей окружности для текущей цели
            circle = plt.Circle((target_x_pos, target_y_pos), target_radius, color='blue', fill=False, linewidth=2)
            plt.gca().add_patch(circle)

            # Отображение метрик на графике рядом с каждой целью
            plt.text(target_x_pos + target_radius + 30, target_y_pos - 85, f'Accuracy: {accuracy:.2f}%', fontsize=8, color='black', bbox=dict(facecolor='white', alpha=0.6))
            plt.text(target_x_pos + target_radius + 30, target_y_pos - 30, f'Hits: {target_hits}/{total_points}', fontsize=8, color='black', bbox=dict(facecolor='white', alpha=0.6))
            plt.text(target_x_pos + target_radius + 30, target_y_pos + 30, f'RMS: {rms_error:.2f}', fontsize=8, color='black', bbox=dict(facecolor='white', alpha=0.6))
            plt.text(target_x_pos + target_radius + 30, target_y_pos + 85, f'Av. dist: {round(mean_distance,2)}', fontsize=8, color='black', bbox=dict(facecolor='white', alpha=0.6))

        # Расчет общих метрик
        total_points_all = sum([metrics['total_points'] for metrics in target_metrics.values()])
        hits_all = sum([metrics['hits'] for metrics in target_metrics.values()])
        mean_distance_all = np.mean([metrics['mean_distance'] for metrics in target_metrics.values()])

        # Средневзвешенная точность
        accuracy_all = sum([metrics['accuracy'] * metrics['total_points'] for metrics in target_metrics.values()]) / total_points_all if total_points_all > 0 else 0

        # Средневзвешенное RMS значение
        rms_error_all = np.sqrt(sum([metrics['rms_error'] ** 2 * metrics['total_points'] for metrics in target_metrics.values()]) / total_points_all) if total_points_all > 0 else 0

       # Отображение общих метрик на графике
        plt.text(0.02 * width, 0.05 * height, f'Average distance to aim: {mean_distance_all:.2f}', fontsize=12, color='black', bbox=dict(facecolor='white', alpha=0.7))
        plt.text(0.02 * width, 0.10 * height, f'Total hits: {total_points_all}', fontsize=12, color='black', bbox=dict(facecolor='white', alpha=0.7))
        plt.text(0.02 * width, 0.15 * height, f'Hits: {hits_all}', fontsize=12, color='black', bbox=dict(facecolor='white', alpha=0.7))
        plt.text(0.02 * width, 0.20 * height, f'Accuracy: {accuracy_all:.2f}%', fontsize=12, color='black', bbox=dict(facecolor='white', alpha=0.7))
        plt.text(0.02 * width, 0.25 * height, f'RMS: {rms_error_all:.2f}', fontsize=12, color='black', bbox=dict(facecolor='white', alpha=0.7))


        # Отображение точек на тепловой карте
        if row_len == 6:
            plt.scatter(x, y, color='red', s=1000, alpha=0.05)
        else:
            plt.scatter(x, y, color='red', s=s, alpha=0.05)


        if fixations:
            # Чтение дополнительных данных для отображения желтых точек
            fixations_data = []
            with open(fixation_path, 'r') as file:
                for line in file:
                    fix_x, fix_y, fix_radius, duration, dispersion, std_dev = line.strip().split(',')
                    s = min(np.pi * ((int(fix_radius)/3) ** 2), 100000000)
                    fixations_data.append((int(fix_x), int(fix_y), float(fix_radius), int(s), float(duration), float(dispersion), float(std_dev)))

            # Преобразование дополнительных данных в DataFrame
            df_fix = pd.DataFrame(fixations_data, columns=['fix_x', 'fix_y', 'fix_radius', 's', 'duration', 'dispersion', 'std_dev'])

            # Нормализация значений длительности для отображения цвета
            min_duration = df_fix['duration'].min()
            max_duration = df_fix['duration'].max()
            norm_duration = (df_fix['duration'] - min_duration) / (max_duration - min_duration)

            # Используем colormap для создания градиента
            custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", ["cyan", "darkblue"])

            # Применение пользовательской цветовой карты
            colors = custom_cmap(norm_duration)


            # Отображение окружностей с градиентными цветами границы
            ax = plt.gca()
            for (fix_x, fix_y, fix_radius, color) in zip(df_fix['fix_x'], df_fix['fix_y'], df_fix['fix_radius'], colors):
                # Создание окружности с заданным цветом границы
                circle = Circle((fix_x, fix_y), fix_radius, color=color, fill=False, hatch='//', linewidth=1, alpha=0.3)
                ax.add_patch(circle)

            # Отображение точек фиксации
            plt.scatter(df_fix['fix_x'], df_fix['fix_y'], color=colors, s=df_fix['s'], alpha=0.2)

            # Настройки градиента 
            gradient = np.linspace(0, 1, 256).reshape(1, -1)
            gradient = np.vstack([gradient] * 5)  # Уменьшение высоты полоски градиента

            # Отображение градиента
            ax.imshow(gradient, aspect='equal', cmap=custom_cmap, extent=[0.02 * width, 0.12 * width, 0.92 * height, 0.95 * height])

            # Добавление аннотаций с крайними значениями длительности
            plt.text(0.025 * width, 0.973 * height, f'{min_duration:.2f} с', fontsize=6, color='black', bbox=dict(facecolor='white', alpha=0.7))
            plt.text(0.115 * width, 0.973 * height, f'{max_duration:.2f} с', fontsize=6, color='black', ha='right', bbox=dict(facecolor='white', alpha=0.7))



        # Настройки графика
        plt.title(f'Визуализация взгляда пользователя (Тестирование)')
        plt.xlabel('Х координаты по ширине')
        plt.ylabel('Y координаты по высоте')
        plt.xlim(0, width)
        plt.ylim(height, 0)
        savename = folder_path + f'/scatter_plot_testing{folder_number}.png'
        plt.savefig(savename, dpi=300)
        self.log(f"Диаграмма рассеивания (тестовое) готова", "SUCCESS", "charts")
        plt.show()
    
    def scatter_plot_testingM(self, folder_path=None, width=1920, height=1080, fixations=False, heatmap=False):
        # Чтение данных из файла

        folder_number = self.get_folder_number(folder_path)
        gaze_path = folder_path + f"/gaze{folder_number}.txt"
        fixation_path = folder_path + f"/fix{folder_number}.txt"

        raw_data = []
        with open(gaze_path, 'r') as file:
            for line in file:
                x, y, r, target_x, target_y, timestamp, time = line.strip().split(',')
                s = min(np.pi * (int(r) ** 2), 2000)
                raw_data.append((int(x), int(y), int(r), int(s), int(target_x), int(target_y), int(timestamp), time))

        df = pd.DataFrame(raw_data, columns=['x', 'y', 'r', 's', 'target_x', 'target_y', 'timestamp', 'time'])

        if heatmap:
            # Извлекаем координаты точек и целей
            x = df['x'].tolist()
            y = df['y'].tolist()

            # Оценка плотности с использованием gaussian_kde
            xy = np.vstack([x, y])
            kde = gaussian_kde(xy, bw_method=0.1)  # Увеличиваем bw_method для большего сглаживания

            # Создаем сетку для вычисления плотности
            xi, yi = np.linspace(0, width, 100), np.linspace(0, height, 100)
            xi, yi = np.meshgrid(xi, yi)
            zi = kde(np.vstack([xi.flatten(), yi.flatten()])).reshape(xi.shape)

            # Дополнительное сглаживание результата для увеличения размеров подсвеченных областей
            zi = gaussian_filter(zi, sigma=3)

            plt.figure(figsize=(16, 9)) 
            # Визуализация тепловой карты с использованием plt.imshow
            plt.imshow(zi, extent=[0, width, 0, height], origin='lower', cmap='jet', interpolation='bilinear', alpha=0.8)


            # Настройки графика
            plt.title(f'Тепловая карта взгляда пользователя на динамический объект)')
            plt.xlabel('Х координаты по ширине')
            plt.ylabel('Y координаты по высоте')
            plt.xlim(0, width)
            plt.ylim(height, 0)
            savename = folder_path + f'/scatter_plot_testingMheatmap{folder_number}.png'
            plt.savefig(savename, dpi=300)
            self.log(f"Тепловая карта (динамический ОУ) готова", "SUCCESS", "charts")
            plt.show()

        # Извлекаем координаты точек и целей
        x = df['x'].tolist()
        y = df['y'].tolist()
        r = df['r'].tolist()
        s = df['s'].tolist()
        target_x = df['target_x'].tolist()
        target_y = df['target_y'].tolist()

        # Создание белого фона
        img_array = np.ones((height, width, 3))

        # Отображение белого фона
        plt.figure(figsize=(16, 9))
        plt.imshow(img_array)

        # Отображение только начальной и конечной позиции цели
        start_target_x = target_x[0]
        start_target_y = target_y[0]
        end_target_x = target_x[-1]
        end_target_y = target_y[-1]
        target_radius = 100  # Радиус синей окружности

        # Отображение окружностей для начальной и конечной цели
        start_circle = plt.Circle((start_target_x, start_target_y), target_radius, color='green', fill=False, linewidth=2)
        end_circle = plt.Circle((end_target_x, end_target_y), target_radius, color='green', fill=False, linewidth=2)
        
        plt.gca().add_patch(start_circle)
        plt.gca().add_patch(end_circle)

        # Отображение траектории взгляда
        plt.scatter(x, y, color='red', s=s, alpha=0.05)

        if fixations:
            # Чтение дополнительных данных для отображения желтых точек
            fixations_data = []
            with open(fixation_path, 'r') as file:
                for line in file:
                    fix_x, fix_y, fix_radius, duration, dispersion, std_dev = line.strip().split(',')
                    s = min(np.pi * ((int(fix_radius)/3) ** 2), 100000000)
                    fixations_data.append((int(fix_x), int(fix_y), float(fix_radius), int(s), float(duration), float(dispersion), float(std_dev)))

            # Преобразование дополнительных данных в DataFrame
            df_fix = pd.DataFrame(fixations_data, columns=['fix_x', 'fix_y', 'fix_radius', 's', 'duration', 'dispersion', 'std_dev'])

            # Нормализация значений длительности для отображения цвета
            min_duration = df_fix['duration'].min()
            max_duration = df_fix['duration'].max()
            norm_duration = (df_fix['duration'] - min_duration) / (max_duration - min_duration)

            # Используем colormap для создания градиента
            custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", ["cyan", "darkblue"])

            # Применение пользовательской цветовой карты
            colors = custom_cmap(norm_duration)


            # Отображение окружностей с градиентными цветами границы
            ax = plt.gca()
            for (fix_x, fix_y, fix_radius, color) in zip(df_fix['fix_x'], df_fix['fix_y'], df_fix['fix_radius'], colors):
                # Создание окружности с заданным цветом границы
                circle = Circle((fix_x, fix_y), fix_radius, color=color, fill=False, hatch='//', linewidth=1, alpha=0.3)
                ax.add_patch(circle)

            # Отображение точек фиксации
            plt.scatter(df_fix['fix_x'], df_fix['fix_y'], color=colors, s=df_fix['s'], alpha=0.2)

            # Настройки градиента 
            gradient = np.linspace(0, 1, 256).reshape(1, -1)
            gradient = np.vstack([gradient] * 5)  # Уменьшение высоты полоски градиента

            # Отображение градиента
            ax.imshow(gradient, aspect='equal', cmap=custom_cmap, extent=[0.02 * width, 0.12 * width, 0.92 * height, 0.95 * height])

            # Добавление аннотаций с крайними значениями длительности
            plt.text(0.025 * width, 0.973 * height, f'{min_duration:.2f} с', fontsize=6, color='black', bbox=dict(facecolor='white', alpha=0.7))
            plt.text(0.115 * width, 0.973 * height, f'{max_duration:.2f} с', fontsize=6, color='black', ha='right', bbox=dict(facecolor='white', alpha=0.7))

        # Список целей, по которым не попал взгляд
        missed_targets_x = []
        missed_targets_y = []

        # Расчет метрик
        distances = []  # Список для хранения расстояний от взгляда до цели
        hits = 0  # Количество попаданий
        total_points = len(x)  # Общее количество точек
        target_valid_points = 0

        for i in range(total_points):
            distance = max(0, np.sqrt((x[i] - target_x[i]) ** 2 + (y[i] - target_y[i]) ** 2) - (r[i] + target_radius))
            if distance <= target_radius * 2:
                target_valid_points += 1
                distances.append(distance)
            # Считаем попаданием, если точка взгляда находится в пределах радиуса цели
            if distance == 0:
                hits += 1
            else:
                # Если это промах, добавляем координаты цели в список пропущенных целей
                missed_targets_x.append(target_x[i])
                missed_targets_y.append(target_y[i])

        # Расчет метрик
        accuracy = (hits / target_valid_points) * 100  # Точность
        mean_distance = np.mean(distances)  # Средняя дистанция
        rms_error = np.sqrt(np.mean(np.array(distances) ** 2))  # RMSE

        # Отображение метрик на графике
        plt.text(0.02 * width, 0.05 * height, f'Средняя дистанция до цели: {mean_distance:.2f} пикселей', fontsize=12, color='black', bbox=dict(facecolor='white', alpha=0.7))
        plt.text(0.02 * width, 0.10 * height, f'Точность: {accuracy:.2f}% ({hits}/{target_valid_points})', fontsize=12, color='black', bbox=dict(facecolor='white', alpha=0.7))
        plt.text(0.02 * width, 0.15 * height, f'RMS ошибка: {rms_error:.2f}', fontsize=12, color='black', bbox=dict(facecolor='white', alpha=0.7))

        # Отображение целей, по которым не попал взгляд, в виде маленьких черных точек
        plt.scatter(missed_targets_x, missed_targets_y, color='black', s=2, label="Missed Targets")

        # Настройки графика
        plt.title(f'Визуализация данных взгляда пользователя по динамическому ОУ')
        plt.xlabel('Х координаты по ширине')
        plt.ylabel('Y координаты по высоте')
        plt.xlim(0, width)
        plt.ylim(height, 0)

        # Сохранение изображения
        savename = folder_path + f'/scatter_plot_testingM{folder_number}.png'
        plt.savefig(savename, dpi=300)
        self.log(f"Диаграмма рассеивания (динамический ОУ) готова", "SUCCESS", "charts")
        plt.show()

    def heatmap_pictures(self, folder_path=None, width=1920, height=1080, title="", xlable="", ylable=""):

        """Метод для построения тепловой карты"""

        folder_number = self.get_folder_number(folder_path)
        gaze_path = folder_path + f"/gaze{folder_number}.txt"


        raw_data = []
        row_len = 0
        with open(gaze_path, 'r') as file:
            for line in file:
                temp = line.strip().split(',')
                row_len = len(temp)
                break
            # print(row_len)
            if row_len == 7:
                for line in file:
                    x, y, r, target_x, target_y, timestamp, time = line.strip().split(',')
                    s = min(np.pi * (int(r) ** 2), 3000)
                    raw_data.append((int(x), int(y), int(r), int(s), int(target_x), int(target_y), int(timestamp), time))
            else:
                for line in file:
                    x, y, r, timestamp, time = line.strip().split(',')
                    s = min(np.pi * (int(r) ** 2), 3000)
                    raw_data.append((int(x), int(y), int(r), int(s), int(timestamp), time))

        if row_len == 7:
            # Преобразование данных в DataFrame
            df = pd.DataFrame(raw_data, columns=['x', 'y', 'r', 's', 'target_x', 'target_y', 'timestamp', 'time'])
        else:
            # Преобразование данных в DataFrame
            df = pd.DataFrame(raw_data, columns=['x', 'y', 'r', 's', 'timestamp', 'time'])


        # Извлекаем координаты точек и целей
        x = df['x'].tolist()
        y = df['y'].tolist()
        if row_len == 7:
            target_x = df['target_x'].tolist()
            target_y = df['target_y'].tolist()

        # Оценка плотности с использованием gaussian_kde
        x = df['x'].tolist()
        y = df['y'].tolist()
        xy = np.vstack([x, y])
        kde = gaussian_kde(xy, bw_method=0.1)

        xi, yi = np.linspace(0, width, 100), np.linspace(0, height, 100)
        xi, yi = np.meshgrid(xi, yi)
        zi = kde(np.vstack([xi.flatten(), yi.flatten()])).reshape(xi.shape)

        # Дополнительное сглаживание
        zi = gaussian_filter(zi, sigma=3)

        # Создание цветовой карты
        colors = [
            (0, 0, 1, 0.05),
            (0, 1, 1, 0.3),
            (0, 1, 0, 0.65),
            (1, 1, 0, 0.7),
            (1, 0, 0, 0.75),
            (0.5, 0, 0, 0.85)
        ]
        cmap = LinearSegmentedColormap.from_list("custom_cmap", colors, N=256)


        if row_len == 7:
            # Получаем список уникальных целей из данных тестирования
            unique_targets = list(set(zip(target_x, target_y)))

            # Создание белого фона
            background_image = np.ones((height, width, 3))

            # Отображение белого фона
            plt.figure(figsize=(16, 9))
            plt.imshow(background_image)

            # Коэф, при котором при ширене окна в 2560 радиус окружности цели будет равен 100
            scale_factor = 0.0390625
            aim_radius = int(width * scale_factor)  # Масштабируем радиус

             # Цикл по уникальным целям для расчета статистики по каждой из них
            for target in unique_targets:

                target_x_pos, target_y_pos = target
                
                # Отображение синей окружности для текущей цели
                circle = plt.Circle((target_x_pos, target_y_pos), aim_radius, color='blue', fill=False, linewidth=2)
                plt.gca().add_patch(circle)

        else:
            # Загрузка изображения фона
            background_image_path = folder_path + f'/image.png'
            background_image = cv2.imread(background_image_path)
            background_image = cv2.cvtColor(background_image, cv2.COLOR_BGR2RGB)
            background_image = cv2.resize(background_image, (width, height))

            plt.figure(figsize=(16, 9))
            plt.imshow(background_image)  # Фон

        plt.imshow(zi, extent=[0, width, 0, height], origin='lower', cmap=cmap, interpolation='bilinear', alpha=0.9)

        # Настройки графика
        plt.title(title)
        plt.xlabel(xlable)
        plt.ylabel(ylable)
        plt.xlim(0, width)
        plt.ylim(height, 0)
        savename = folder_path + f'/heatmap{folder_number}.png'
        plt.savefig(savename, dpi=300)
        self.log(f"Тепловая карта готова", "SUCCESS", "charts")
        plt.show()
    

    def radius_hist(self, folder_path=None, title="", xlable="", ylable=""):

        """Метод для построения гистограммы распределения радиусов зоны взгляда"""

        folder_number = self.get_folder_number(folder_path)
        gaze_path = folder_path + f"/gaze{folder_number}.txt"

        raw_data = []
        with open(gaze_path, 'r') as file:
            for line in file:
                arr = line.strip().split(',')
                raw_data.append(int(arr[2]))

        # Преобразование данных в DataFrame
        df = pd.DataFrame(raw_data, columns=['r'])

        # Извлечение данных радиусов
        radii = df['r'].values

        # Построение гистограммы
        plt.figure(figsize=(12, 6))
        plt.hist(radii, bins=30, color='blue', alpha=0.7, edgecolor='black', density=True)
        plt.title(title)
        plt.xlabel(xlable)
        plt.ylabel(ylable)
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Сохранение изображения
        savename = folder_path + f'/radius_hist{folder_number}.png'
        plt.savefig(savename, dpi=300)
        self.log(f"Гистограмма радиусов зон взгляда готова", "SUCCESS", "charts")
        plt.show()


if __name__ == "__main__":
    charts = Charts()
    charts.scatter_plot_pictures(gazeData="/Users/noname/Desktop/tracker/old_tracker/tests/gazeTracktion2/gaze3.txt")