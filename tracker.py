import os
import cv2
import mediapipe as mp
from statistics import mean
import numpy as np
import time
from datetime import datetime
from collections import deque
from scipy.spatial import distance as dist
import colorama

class EyeTracker:
    def __init__(self, camera=0, res="1280x1080", cam_res=None, fixation=True, blink=True, fast=True, folder_path=None,file_path=None, duration=5, ma_trshhd=0.65, ma_width=5, exp_koef=0.5):
        
        colorama.init()  # Инициализируем colorama

        # Переменная главного цикла
        self.window_holder = True

        # Для обработки нажатых клавиш
        self.key = None

        # Ширина и высота окна
        self.screen_w, self.screen_h = map(int, res.split('x'))

        self.cam = self.open_camera(camera, fast, cam_res)
        self.log(f"Установленное разрешение вебкамеры: {self.cam.get(cv2.CAP_PROP_FRAME_WIDTH)}x{self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT)}", "INFO", "tracker")

        # Модель FaceMash от Mediapipe
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
        
        # Переменный путей
        self.folder_path = folder_path
        self.file_path = file_path

        # Служебные переменные-флаги
        self.img_read = False
        self.calibrated = False

        # Счетчик имени папки
        self.save_counter = 0
        self.save_folder_name = "gazeTracktion0"
        
        # Переменная продолжительности испытания
        self.duration = duration

        # Калибровка и другие переменные
        self.frame_center_x = self.screen_w // 2
        self.frame_center_y = self.screen_h // 2
        self.frame_left_top_corner_x = 0
        self.frame_left_top_corner_y = 0
        self.frame_right_bottom_corner_x = self.screen_w
        self.frame_right_bottom_corner_y = self.screen_h
        self.focused = 0
        self.left_top_corner_x = None
        self.left_top_corner_y = None
        self.right_bottom_corner_x = None
        self.right_bottom_corner_y = None
        self.nose_calib_x = []
        self.nose_calib_y = []
        self.nose_calib_mean_x = None
        self.nose_calib_mean_x = None

        # Параметры окружности зоны взгляда
        self.gaze_area_color = (0, 255, 0)
        self.gaze_area_border = 2
                
        # Индексы точек глаз для определения морганий
        self.left_eye_indices = [468, 33, 160, 158, 133, 153, 144]
        self.right_eye_indices = [473, 362, 385, 387, 263, 373, 380]
        self.left_eye_center = None
        self.right_eye_center = None
        self.nose = None

        # Очередь для хранения последних позиций взгляда для сглаживания (МА)
        self.smooth_x = deque(maxlen=ma_width)
        self.smooth_y = deque(maxlen=ma_width)
        self.smooth_threshold = ma_trshhd
        self.smooth_frame_pos_x = None
        self.smooth_frame_pos_y = None

        # Параметры для сглаживания перемещения точки взгляда
        self.alpha = exp_koef  # Коэффициент сглаживания 35
        self.smooth_frame_pos_x_exp = None
        self.smooth_frame_pos_y_exp = None

        # Параметры для радиуса круга взгляда
        self.min_radius = 10           # Минимальный радиус круга 10
        self.max_radius = 60           # Максимальный радиус круга

        # Переменные для подсчета морганий
        self.blink = blink
        self.blink_counter = 0
        self.eye_closed_frames = 0
        self.EAR_THRESHOLD = 0.21  # Пороговое значение для определения моргания
        self.EAR_CONSEC_FRAMES = 2  # Количество последовательных кадров, в которых глаз должен быть закрыт

        # Параметры для отслеживания фиксаций
        self.FIXATION_DURATION = 0.3  # Минимальная длительность фиксации в секундах
        self.FIXATION_AREA_RADIUS = 150  # Радиус области фиксации в пикселях

        # Переменные для фиксаций
        self.fixation = fixation
        self.current_fixation = None
        self.fixation_start_time = None
        self.fixations = []
        self.fixation_gaze_points = None

        # Тестирование
        self.testing = False
        self.testingX = False
        self.tested = False
        self.testingMove = False
        self.testedM = False
        self.start_testing_time = None
        self.circle_index = 0
        self.pic_testing = None
        self.image_index = 0
        self.pic_frame = None
        self.pic_frame_orig = None
        if self.file_path != None:
            self.picture_test = True
        else:
            self.picture_test = False

    def show_loader(self):
        """Функция для отображения экрана загрузки"""
        width, height = 500, 100
        loader_img = np.zeros((height, width, 3), dtype=np.uint8)
        
        text = "loading, wait..."
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(text, font, 1, 2)[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height - text_size[1]) // 2
        
        cv2.putText(loader_img, text, (text_x, text_y+20), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow('Eye tracker', loader_img)
        cv2.waitKey(1)  # Нужно, чтобы окно обновилось
    
    def open_camera(self, c, f, cam_res):
        """Функция для открытия камеры"""
        self.show_loader()  # Показываем загрузочный экран
        
        # Режим подключения к камере
        if f:
            cam = cv2.VideoCapture(c, cv2.CAP_DSHOW)
            if cam_res != None:
                w, h = map(int, cam_res.split('x'))
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        else:
            cam = cv2.VideoCapture(c)
            if cam_res != None:
                w, h = map(int, cam_res.split('x'))
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        
        start_time = time.time()
        while not cam.isOpened():
            if time.time() - start_time > 100:  # Таймаут 100 секунд
                self.log(f"Ошибка подключения к камере... (timeout)", "ERROR", "tracker")
                cv2.destroyWindow('Eye tracker')
                return
        
        # cv2.destroyWindow("Loader window")  # Закрываем загрузочный экран
        return cam
    

    # Функция отрисовки точек, полученных от модели FaceMesh Mediapipe
    def draw_landmarks(self, landmarks, frame_w, frame_h):
        
        left_eye_landmarks = []
        right_eye_landmarks = []
        
        # Извлекаем координаты левого глаза EAR
        for idx in self.left_eye_indices:
            x = landmarks[idx].x * frame_w
            y = landmarks[idx].y * frame_h
            if idx == 468:
                cv2.circle(self.frame, (int(x), int(y)), 2, (0, 0, 255))
            else:
                left_eye_landmarks.append((x, y))
                cv2.circle(self.frame, (int(x), int(y)), 2, (0, 255, 0), -1)

        # Извлекаем координаты правого глаза EAR
        for idx in self.right_eye_indices:
            x = landmarks[idx].x * frame_w
            y = landmarks[idx].y * frame_h
            if idx == 473:
                cv2.circle(self.frame, (int(x), int(y)), 2, (0, 0, 255))
            else:
                right_eye_landmarks.append((x, y))
                cv2.circle(self.frame, (int(x), int(y)), 2, (0, 255, 0), -1)
        
        # Рисуем кончик носа
        self.nose = landmarks[1]
        cv2.circle(self.frame, (int(self.nose.x * frame_w), int(self.nose.y * frame_h)), 2, (0, 255, 255), 2)
        if self.picture_test:
            cv2.circle(self.pic_frame, (int(self.nose.x * frame_w), int(self.nose.y * frame_h)), 2, (0, 255, 255), 2)

        self.left_eye_center, self.right_eye_center = landmarks[468], landmarks[473]

        return left_eye_landmarks, right_eye_landmarks
    

    # Функция калибровки трекера по взгляду пользователя
    def calibrate(self, frame_w, frame_h):

        cv2.circle(self.frame, (self.frame_center_x, self.frame_center_y), 2, (0, 0, 255), 2)

        # Калибровка по центру
        if self.focused == 0:
            cv2.circle(self.frame, (self.frame_center_x, self.frame_center_y), 10, (0, 0, 255), 10)
            cv2.putText(self.frame, "look at CENTER and press SPACE", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 200, 0), 2)
        
            if self.key == ord(' '):
                self.focused += 1
        
        # Калибровка по левому верхнему углу
        elif self.focused == 1:
            cv2.circle(self.frame, (self.frame_left_top_corner_x+10, self.frame_left_top_corner_y+10), 10, (0, 0, 255), 10)
            cv2.putText(self.frame, "look at UPPER LEFT and press SPACE", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 200, 0), 2)
            
            if self.key == ord(' '):
                self.left_top_corner_x, self.left_top_corner_y = self.calibrate_coords("Координаты глаз при калибровке по левому верхнему углу: ")
        
        # Калибровка по правому нижнему углу
        elif self.focused == 2:
            cv2.circle(self.frame, (self.frame_right_bottom_corner_x-10, self.frame_right_bottom_corner_y-10), 10, (0, 0, 255), 10)
            cv2.putText(self.frame, "look at BOTTOM RIGHT and press SPACE", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 200, 0), 2)
            
            if self.key == ord(' '):
                self.right_bottom_corner_x, self.right_bottom_corner_y = self.calibrate_coords("Координаты глаз при калибровке по правому нижниму углу: ")
                # Точка калибровки носа
                self.nose_calib_mean_x = int(mean(self.nose_calib_x) * frame_w)
                self.nose_calib_mean_y = int(mean(self.nose_calib_y) * frame_h)

                self.calibrated = True
        

    # Получение координат зрачков и из рассчет (для калибровки)
    def calibrate_coords(self, text):
        pulp_mid_x = (self.left_eye_center.x + self.right_eye_center.x) / 2
        pulp_mid_y = (self.left_eye_center.y + self.right_eye_center.y) / 2
        self.nose_calib_x.append(self.nose.x)
        self.nose_calib_y.append(self.nose.y)
        self.log(f"{text} сохранены", "INFO", "tracker")
        # print(text, pulp_mid_x, pulp_mid_y, "Нос:", self.nose_calib_x, self.nose_calib_y)
        self.focused += 1
        return pulp_mid_x, pulp_mid_y

    # Функция 1 рассчета метрики EAR для определения моргания 
    def EAR(self, left_eye_landmarks, right_eye_landmarks):

        left_EAR = self.calculate_EAR(left_eye_landmarks)
        right_EAR = self.calculate_EAR(right_eye_landmarks)
        avg_EAR = (left_EAR + right_EAR) / 2.0

        # Логика обнаружения морганий
        if avg_EAR < self.EAR_THRESHOLD:
            self.eye_closed_frames += 1
        else:
            if self.eye_closed_frames >= self.EAR_CONSEC_FRAMES:
                self.blink_counter += 1
            self.eye_closed_frames = 0


    # Функция 2 рассчета метрики EAR для определения моргания 
    def calculate_EAR(self, eye_landmarks):
        
        A = dist.euclidean(eye_landmarks[1], eye_landmarks[5])  # Вычисляем расстояния между вертикальными точками глаза
        B = dist.euclidean(eye_landmarks[2], eye_landmarks[4])  # Вычисляем расстояния между вертикальными точками глаза
        C = dist.euclidean(eye_landmarks[0], eye_landmarks[3])# Вычисляем расстояние между горизонтальными точками глаза

        return (A + B) / (2.0 * C)  # Вычисляем соотношение сторон глаза (EAR)
    

    # Функция рассчета взгляда пользователя
    def calculate_gaze(self, frame_w, frame_h):

        # Получения координа глаз в кадре
        pos_x = (self.left_eye_center.x + self.right_eye_center.x) / 2
        pos_y = (self.left_eye_center.y + self.right_eye_center.y) / 2

        # Рассчет координат взгляда
        frame_pos_x = (pos_x - self.left_top_corner_x) * self.frame_right_bottom_corner_x / (self.right_bottom_corner_x - self.left_top_corner_x)
        frame_pos_y = (pos_y - self.left_top_corner_y) * self.frame_right_bottom_corner_y / (self.right_bottom_corner_y - self.left_top_corner_y)

        # Заполнение очередей для МА
        if len(self.smooth_x) == self.smooth_x.maxlen:
            median_x = mean(self.smooth_x)
            median_y = mean(self.smooth_y)
            if (abs(frame_pos_x - median_x) > self.frame_right_bottom_corner_x * self.smooth_threshold) or (abs(frame_pos_y - median_y) > self.frame_right_bottom_corner_y * self.smooth_threshold):
                # Очистить очередь, если новое значение отличается более чем на smooth_threshold
                self.smooth_x.clear()
                self.smooth_y.clear()
            self.smooth_x.append(frame_pos_x)
            self.smooth_y.append(frame_pos_y)
        else:
            # Добавляем текущие значения в очередь координат взгляда для сглаживания
            self.smooth_x.append(frame_pos_x)
            self.smooth_y.append(frame_pos_y)

        # Рассчитываем усредненные значения взгляда (МА)
        self.smooth_frame_pos_x = int(mean(self.smooth_x))
        self.smooth_frame_pos_y = int(mean(self.smooth_y))

        # Применяем экспоненциальное сглаживание на перемещение зоны взгляда по экрану
        if self.smooth_frame_pos_x_exp is None:
            self.smooth_frame_pos_x_exp = self.smooth_frame_pos_x
            self.smooth_frame_pos_y_exp = self.smooth_frame_pos_y
        else:
            self.smooth_frame_pos_x_exp = int(self.alpha * self.smooth_frame_pos_x + (1 - self.alpha) * self.smooth_frame_pos_x_exp)
            self.smooth_frame_pos_y_exp = int(self.alpha * self.smooth_frame_pos_y + (1 - self.alpha) * self.smooth_frame_pos_y_exp)

        # Вычисляем стандартное отклонение по X и Y для построение окружности зоны взгляда
        std_x = np.std(self.smooth_x)
        std_y = np.std(self.smooth_y)

        # Вычисляем общий разброс и определяем радиус круга
        spread = np.sqrt(std_x**2 + std_y**2)
        radius = int(spread / 2)

        # Ограничиваем радиус минимальным и максимальным значениями
        radius = max(self.min_radius, min(radius, self.max_radius))

        self.smooth_frame_pos_x = self.smooth_frame_pos_x_exp
        self.smooth_frame_pos_y = self.smooth_frame_pos_y_exp

        # Рисуем круг на фрейме
        cv2.circle(self.frame, (self.smooth_frame_pos_x, self.smooth_frame_pos_y), radius, self.gaze_area_color, self.gaze_area_border)
        # Выводим координаты сглаженной позиции взгляда
        cv2.putText(self.frame, f'{self.smooth_frame_pos_x} {self.smooth_frame_pos_y}', (60, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_4)

        if self.picture_test:
            cv2.circle(self.pic_frame, (self.smooth_frame_pos_x, self.smooth_frame_pos_y), radius, self.gaze_area_color, self.gaze_area_border)
            cv2.putText(self.pic_frame, f'{self.smooth_frame_pos_x} {self.smooth_frame_pos_y}', (60, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_4)

        # Получение текущего времени  
        time_string = datetime.now().strftime("%M:%S.%f")[:-3]
        timestamp = int(time.time())

        # Сохранение данных взгляда в соответствующие файлы
        if (0 <= self.smooth_frame_pos_x <= self.screen_w) and (0 <= self.smooth_frame_pos_y <= self.screen_h):

            if self.testing or self.testingX:
                try:
                    with open(f'{self.folder_path}/{self.save_folder_name}/gaze{self.save_counter}.txt', 'a') as file:
                        file.write(f'{self.smooth_frame_pos_x},{self.smooth_frame_pos_y},{radius},{int(self.current_position[0]*frame_w)},{int(self.current_position[1]*frame_h)},{timestamp},{time_string}\n')
                except Exception as e:
                    self.log(f"Ошибка при записи в {self.folder_path}/{self.save_folder_name}/gaze{self.save_counter}.txt: {e}", "ERROR", "tracker")
            if self.testingMove:
                try:
                    with open(f'{self.folder_path}/{self.save_folder_name}/gaze{self.save_counter}.txt', 'a') as file:
                        file.write(f'{self.smooth_frame_pos_x},{self.smooth_frame_pos_y},{radius},{int(self.current_position[0])},{int(self.current_position[1])},{timestamp},{time_string}\n')
                except Exception as e:
                    self.log(f"Ошибка при записи в {self.folder_path}/{self.save_folder_name}/gaze{self.save_counter}.txt: {e}", "ERROR", "tracker")
            if self.picture_test:
                try:
                    with open(f'{self.folder_path}/{self.save_folder_name}/gaze{self.save_counter}.txt', 'a') as file:
                        file.write(f'{self.smooth_frame_pos_x},{self.smooth_frame_pos_y},{radius},{timestamp},{time_string}\n')
                except Exception as e:
                    self.log(f"Ошибка при записи в {self.folder_path}/{self.save_folder_name}/gaze{self.save_counter}.txt: {e}", "ERROR", "tracker")

    # Функция рассчета указателя зоны взгляда (которая ушла за пределы видимой зоны окна)
    def draw_gaze_direction(self, gaze_x, gaze_y):

        # Центр экрана
        center_x = self.frame_center_x
        center_y = self.frame_center_y

        # Проверка, находится ли расчетная точка взгляда за границами экрана
        if 0 <= gaze_x <= self.frame_right_bottom_corner_x and 0 <= gaze_y <= self.frame_right_bottom_corner_y:
            return  # Точка внутри экрана, выход

        # Определяем разницу по X и по Y от центра экрана
        dx = gaze_x - center_x
        dy = gaze_y - center_y

        # Определяем крутость наклона луча из центра до точки взгляда (отношение изменения ординат к изменению абсцисс)
        if dx != 0:
            slope = dy / dx
        else:
            slope = float('inf')  # Если dx = 0, линия вертикальная

        # Взгляд направлен в право
        if dx > 0:
            intersect_x = self.frame_right_bottom_corner_x                                  # Пересечение с правой границей
            intersect_y = center_y + slope * (self.frame_right_bottom_corner_x - center_x)  # Рассчет высоты пересечения
        else:
            intersect_x = 0                                     # Пересечение с левой границей
            intersect_y = center_y + slope * (0 - center_x)     # Рассчет высоты пересечения

        # Проверяем, если пересечение по Y выходит за верх или низ экрана
        if not (0 <= intersect_y <= self.frame_right_bottom_corner_y):
            if dy > 0:
                intersect_y = self.frame_right_bottom_corner_y  # Пересечение с нижней границей
                intersect_x = center_x + (self.frame_right_bottom_corner_y - center_y) / slope
            else:
                intersect_y = 0                                 # Пересечение с верхней границей
                intersect_x = center_x + (0 - center_y) / slope

        # Рассчитываем расстояние от расчетной точки до границы экрана
        distance_to_border = np.sqrt((gaze_x - intersect_x) ** 2 + (gaze_y - intersect_y) ** 2)

        # Перестроение радиуса точки в зависимости от расстояния до границы
        max_distance = 3500
        min_radius = 10
        max_radius = 50
        radius = max_radius - (max_radius - min_radius) * min(distance_to_border, max_distance) / max_distance
        radius = int(radius)  # Преобразуем в целое число для рисования

        # Рисуем точку на пересечении границы экрана
        cv2.circle(self.frame, (int(intersect_x), int(intersect_y)), radius, (0, 0, 255), -1)
        if self.picture_test:
            cv2.circle(self.pic_frame, (int(intersect_x), int(intersect_y)), radius, (0, 0, 255), -1)
    

    # Функция рассчета фиксаций взгляда пользователя
    def calculate_fixation(self):

        current_time = time.time()
        current_gaze = (self.smooth_frame_pos_x, self.smooth_frame_pos_y)

        # Проверяем, находится ли взгляд внутри границ экрана
        if (0 <= int(current_gaze[0]) <= self.screen_w) and (0 <= int(current_gaze[1]) <= self.screen_h):
            # Если текущая фиксация не существует, инициализируем новую
            if self.current_fixation is None:
                self.current_fixation = current_gaze
                self.fixation_start_time = current_time
                self.fixation_gaze_points = []  # Инициализация массива для координат взгляда
            else:
                # Рассчитываем расстояние от текущей точки взгляда до начальной точки фиксации
                distance = dist.euclidean(current_gaze, self.current_fixation)
                duration = current_time - self.fixation_start_time

                # Если взгляд находится в пределах радиуса, продолжаем удерживать фиксацию
                if distance <= self.FIXATION_AREA_RADIUS:
                    # Добавляем текущие координаты взгляда в массив
                    self.fixation_gaze_points.append(current_gaze)
                    if duration >= self.FIXATION_DURATION:
                        self.gaze_area_color = (0, 0, 255)
                        self.gaze_area_border = 4
                else:
                    # Взгляд вышел за пределы радиуса, проверяем длительность фиксации
                    if duration >= self.FIXATION_DURATION and self.fixation_gaze_points:

                        # Разделяем координаты на X и Y
                        x_coords = [point[0] for point in self.fixation_gaze_points]
                        y_coords = [point[1] for point in self.fixation_gaze_points]

                        # Средние координаты фиксации
                        mean_x = np.mean(x_coords)
                        mean_y = np.mean(y_coords)

                        # Вычисляем расстояния от каждой точки до средней точки
                        distances = [np.sqrt((x - mean_x) ** 2 + (y - mean_y) ** 2) for x, y in self.fixation_gaze_points]

                        # Рассчитываем дисперсию и стандартное отклонение этих расстояний
                        variance = np.var(distances)
                        std_dev = np.std(distances)

                        # Радиус рассеивания (максимальное расстояние от средней точки)
                        radius = max(distances)

                        self.fixations.append((int(mean_x), int(mean_y)))
 
                        # Сохраняем фиксацию в файл
                        if self.picture_test:
                            try:
                                with open(f'{self.folder_path}/{self.save_folder_name}/fix{self.save_counter}.txt', 'a') as file:
                                    file.write(f'{int(mean_x)},{int(mean_y)},{int(radius)},{duration},{variance},{std_dev}\n')
                            except Exception as e:
                                self.log(f"Ошибка при записи в {self.folder_path}/{self.save_folder_name}/gaze{self.save_counter}.txt: {e}", "ERROR", "tracker")
                        if self.testing or self.testingX:
                            try:
                                with open(f'{self.folder_path}/{self.save_folder_name}/fix{self.save_counter}.txt', 'a') as file:
                                    file.write(f'{int(mean_x)},{int(mean_y)},{int(radius)},{duration},{variance},{std_dev}\n')
                            except Exception as e:
                                self.log(f"Ошибка при записи в {self.folder_path}/{self.save_folder_name}/fix{self.save_counter}.txt: {e}", "ERROR", "tracker")
                        elif self.testingMove:
                            try:
                                with open(f'{self.folder_path}/{self.save_folder_name}/fix{self.save_counter}.txt', 'a') as file:
                                    file.write(f'{int(mean_x)},{int(mean_y)},{int(radius)},{duration},{variance},{std_dev}\n')
                            except Exception as e:
                                self.log(f"Ошибка при записи в {self.folder_path}/{self.save_folder_name}/fix{self.save_counter}.txt: {e}", "ERROR", "tracker")

                    # Сбрасываем текущую фиксацию, так как взгляд вышел за пределы радиуса
                    self.current_fixation = None
                    self.fixation_start_time = None
                    self.fixation_gaze_points = None  # Очищаем массив точек взгляда
                    self.gaze_area_color = (0, 255, 0)
                    self.gaze_area_border = 2


    # Функция отрисовки цели-окружности на фрейме
    def draw_circle_with_number(self, center, number):
        
        # Коэф, при котором при ширене окна в 2560 радиус окружности цели будет равен 100
        scale_factor = 0.0390625
        self.aim_radius = int(self.screen_w * scale_factor)  # Масштабируем радиус

        cv2.circle(self.frame, center, self.aim_radius, (0, 255, 0), 2)  # Рисуем зеленый круг с границей 2 без заливки
        cv2.putText(self.frame, str(number), (center[0] - 10, center[1] + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2) # Выводим порядковый номер круга


    # Функция проведения тестирования со статичными целями по квадрату 
    def static_testing_1(self):

        current_time = time.time()
        elapsed_time = current_time - self.start_testing_time

        # Позиции для кругов тестирования
        positions = [
            (0.25, 0.25),  # Первая четверть (верхний левый угол)
            (0.75, 0.25),  # Вторая четверть (верхний правый угол)
            (0.75, 0.75),  # Третья четверть (нижний правый угол)
            (0.25, 0.75),  # Четвертая четверть (нижний левый угол)
        ]

        # Показываем новый круг каждые 3 секунды
        if self.circle_index < len(positions):
            if elapsed_time >= 3 * self.circle_index:
                self.current_position = positions[self.circle_index]
                # Очищаем экран от предыдущего круга
                height, width, _ = self.frame.shape
                center_x = int(positions[self.circle_index][0] * width)
                center_y = int(positions[self.circle_index][1] * height)
                self.draw_circle_with_number((center_x, center_y), self.circle_index + 1)

        # Переходим к следующему кругу каждые 3 секунды
        if elapsed_time >= (self.circle_index + 1) * 3:
            self.circle_index += 1
        
        # Когда все круги показаны, возвращаемся к обычному режиму
        if self.circle_index >= len(positions):
            self.testing = False
            self.tested = True
            self.log(f"Тестирование по квадрату завершено", "INFO", "tracker")
            # Записываем разрешение экрана в файл
            with open(f'{self.folder_path}/{self.save_folder_name}/res.txt', "w") as file:
                file.write(f"({self.screen_w},{self.screen_h})")
            self.key = ord('q')

    # Функция проведения тестирования со статичными целями по кресту (Х) 
    def static_testing_2(self):

        current_time = time.time()
        elapsed_time = current_time - self.start_testing_time

        # Позиции для кругов тестирования в требуемой последовательности
        positions = [
            (0.5, 0.5),  # Центр экрана
            (0.25, 0.25),  # Левый верхний угол
            (0.5, 0.5),  # Центр экрана
            (0.75, 0.25),  # Правый верхний угол
            (0.5, 0.5),  # Центр экрана
            (0.75, 0.75),  # Правый нижний угол
            (0.5, 0.5),  # Центр экрана
            (0.25, 0.75),  # Левый нижний угол
        ]

        # Показываем новый круг каждые 3 секунды
        if self.circle_index < len(positions):
            if elapsed_time >= 3 * self.circle_index:
                self.current_position = positions[self.circle_index]
                # Очищаем экран от предыдущего круга
                height, width, _ = self.frame.shape
                center_x = int(positions[self.circle_index][0] * width)
                center_y = int(positions[self.circle_index][1] * height)
                self.draw_circle_with_number((center_x, center_y), self.circle_index + 1)

        # Переходим к следующему кругу каждые 3 секунды
        if elapsed_time >= (self.circle_index + 1) * 3:
            self.circle_index += 1

        # Когда все круги показаны, возвращаемся к обычному режиму
        if self.circle_index >= len(positions):
            self.testingX = False
            self.tested = True
            self.log(f"Тестирование по X завершено", "INFO", "tracker")
            # Записываем разрешение экрана в файл
            with open(f'{self.folder_path}/{self.save_folder_name}/res.txt', "w") as file:
                file.write(f"({self.screen_w},{self.screen_h})")
            self.key = ord('q')

    # Функция проведения тестирования с динамическим объектом управления
    def moving_testing(self):

        current_time = time.time()
        elapsed_time = current_time - self.start_testing_time

        # Перемещение объекта из первой четверти в третью за 5 секунд
        if elapsed_time <= 5:
            # Вычисляем текущую позицию объекта
            start_pos = (int(self.screen_w * 0.25), int(self.screen_h * 0.25))  # Начальная позиция
            end_pos = (int(self.screen_w * 0.75), int(self.screen_h * 0.75))    # Конечная позиция
            progress = elapsed_time / 5  # Прогресс перемещения (0.0 до 1.0)

            # Интерполяция для вычисления текущей позиции
            current_x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress)
            current_y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress)
            self.current_position = [current_x, current_y]
            # Отображение круга в текущей позиции
            self.draw_circle_with_number((current_x, current_y), 1)

        else:
            # Завершаем тест после 5 секунд
            self.testingMove = False
            self.testedM = True
            # Записываем разрешение экрана в файл
            with open(f'{self.folder_path}/{self.save_folder_name}/res.txt', "w") as file:
                file.write(f"({self.screen_w},{self.screen_h})")
            self.log(f"Тестирование с движущийся целью (динамический ОУ) завершено", "INFO", "tracker")
            self.key = ord('q')
    

    # Функция проведения испытания с выбранным изображением
    def show_picture(self):

        if self.img_read != True:

            self.log(f"Начинается испытание и запись данных взгляда пользователя на изображение", "INFO", "tracker")

            # обратный отсчет до начала испытания
            self.countdown()

            # Определение номера папки для испытания
            while os.path.exists(os.path.join(self.folder_path, self.save_folder_name)):
                self.save_counter += 1
                self.save_folder_name = f"gazeTracktion{self.save_counter}"
                
            # Создаём новую папку под испытание
            os.makedirs(os.path.join(self.folder_path, self.save_folder_name))

            image = cv2.imread(self.file_path)
            self.pic_frame_orig = cv2.resize(image, (self.screen_w, self.screen_h))
            self.pic_frame = self.pic_frame_orig.copy()

            # Показываем кадр в окне
            cv2.imshow('Eye tracker', self.pic_frame)

            self.img_read = True
            self.start_testing_time = time.time()
        
        current_time = time.time()
        elapsed_time = current_time - self.start_testing_time

        cv2.putText(self.pic_frame, f'time left: {round(self.duration-elapsed_time, 2)}', (60, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_4)
        
        if elapsed_time > self.duration:

            cv2.imwrite(f'{self.folder_path}/{self.save_folder_name}/image.png', self.pic_frame_orig)
            # Записываем разрешение экрана в файл
            with open(f'{self.folder_path}/{self.save_folder_name}/res.txt', "w") as file:
                file.write(f"({self.screen_w},{self.screen_h})")
            # Завершаем тестирование после просмотра всех изображений
            self.picture_test = False
            self.log(f"Проведение испытания для изображения изображения завершено", "INFO", "tracker")
            self.key = ord('q')
    
    # Функция возврата параметров трекера работы трекера в ГУИ
    def callback_data(self):

        data = {
            "folder_name":self.save_folder_name,
            "width":self.screen_w,
            "height":self.screen_h,
            "tested":self.tested,
            "testedM":self.testedM
        }
        return data
    

    # Функция для отрисовки текста на фрейме
    def draw_text(self, frame, text, position, font_scale=2, thickness=3, color=(255, 255, 255)):
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)


    # Функция организации обратного отсчета для испытаний
    def countdown(self):

        # Запуск обратного отсчета
        for count in range(3, -1, -1):
            # Создаем черный фон
            frame = np.zeros((self.screen_h, self.screen_w, 3), dtype=np.uint8)

            # Отображаем текущую цифру обратного отсчета (по центру)
            if count > 0:
                self.draw_text(frame, str(count), (self.screen_w // 2 - 30, self.screen_h // 2), font_scale=4, thickness=5, color=(255, 255, 255))

            # Показываем кадр в окне
            cv2.imshow('Eye tracker', frame)

            cv2.waitKey(500)
    
    def log(self, message, level="INFO", source="NA"):
        """Функция для красивого вывода логов"""
        colors = {
            "INFO": colorama.Fore.CYAN,   # Голубой
            "WARNING": colorama.Fore.YELLOW,  # Желтый
            "ERROR": colorama.Fore.RED,   # Красный
            "SUCCESS": colorama.Fore.GREEN,  # Зеленый
        }
        
        now = datetime.now().strftime("%H:%M:%S")  # Получаем текущее время (часы:минуты:секунды)
        color = colors.get(level, colorama.Fore.WHITE)  # Получаем цвет (по умолчанию белый)
        
        print(f"{color}[{now}] [{level}] ({source}) {message}{colorama.Style.RESET_ALL}")


    # ГЛАВНЫЙ РАБОЧИЙ ЦИКЛ ПРОГРАММЫ 
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    def start(self):
        self.log(f"Трекер запущен и начал работу", "INFO", "tracker")
        # Главный цикл
        while self.window_holder:
            
            _, self.frame = self.cam.read()                         # Получаем кадр с вебки
            frame_h, frame_w, _ = self.frame.shape

            # Вычисляем новую ширину кадра, сохраняя соотношение сторон
            new_frame_h = self.screen_h  # Высота кадра будет равна высоте изображения
            aspect_ratio = frame_w / frame_h  # Соотношение сторон веб-камеры
            new_frame_w = int(new_frame_h * aspect_ratio)  # Новая ширина кадра

            self.frame = cv2.flip(self.frame, 1)                    # Отражаем кадр

            # Масштабируем кадр с сохранением пропорций
            self.frame = cv2.resize(self.frame, (new_frame_w, new_frame_h))
            # Создаем черный фон (канвас) с размерами изображения
            canvas = np.zeros((self.screen_h, self.screen_w, 3), dtype=np.uint8)

            # Вычисляем координаты для центрирования по ширине
            x_offset = (self.screen_w - new_frame_w) // 2

            # Вставляем кадр с веб-камеры по центру (с чёрными полями, если нужно)
            canvas[:, x_offset:x_offset+new_frame_w] = self.frame

            self.frame = canvas

            frame_h, frame_w, _ = self.frame.shape

            # self.frame = cv2.resize(self.frame, (self.screen_w, self.screen_h))       # Ресайз под разрешение
            rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            output = self.face_mesh.process(rgb_frame)              # Получаем разметку лица
            landmark_points = output.multi_face_landmarks
            

            if self.picture_test and self.img_read:
                self.pic_frame = self.pic_frame_orig.copy()

            # Если есть лицо в кадре
            if landmark_points:

                # Выводим ключевые точки лица на экран
                left_eye_landmarks, right_eye_landmarks = self.draw_landmarks(landmark_points[0].landmark, frame_w, frame_h)

                # Вывод центра кадра во время калибровки
                if self.focused < 3:
                    # Производим калибровку
                    self.calibrate(frame_w, frame_h)

                else:

                    # Вычисление EAR для обоих глаз
                    if self.blink:
                        self.EAR(left_eye_landmarks, right_eye_landmarks)

                        # Отображаем количество морганий на кадре
                        cv2.putText(self.frame, f'Blinks: {self.blink_counter}', (60, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2, cv2.LINE_AA)

                    # Отображаем точку калибровки носа
                    cv2.circle(self.frame, (self.nose_calib_mean_x, self.nose_calib_mean_y), 2, (0, 0, 255), 2)
                    if self.picture_test:
                        cv2.circle(self.pic_frame, (self.nose_calib_mean_x, self.nose_calib_mean_y), 2, (0, 0, 255), 2)

                    # Рассчитываем точку взгляда
                    self.calculate_gaze(frame_w, frame_h)

                    # Рассчитываем фиксации взгляда
                    if self.fixation:
                        self.calculate_fixation()

                    # Отрисовываем точку взгляда
                    self.draw_gaze_direction(self.smooth_frame_pos_x_exp, self.smooth_frame_pos_y_exp)
            

            # ОБРАБОТКА НАЖАТИЯ КЛАВИШ 
            # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

            # Ожидание нажатия клавиши
            self.key = cv2.waitKey(1) & 0xFF

            # Если нажата 'k' - Начать калибровку
            if self.key == ord('k') and not self.testing:
                self.focused = 0
                self.nose_calib_x = []
                self.nose_calib_y = []
                self.fixations = []

            # Если нажата 't' - Начать тестирование
            elif self.key == ord('t') and not self.testing:

                # Определение имени для папки тестирования
                self.save_folder_name = "Test_"+self.save_folder_name
                while os.path.exists(os.path.join(self.folder_path, self.save_folder_name)):
                    self.save_counter += 1
                    self.save_folder_name = f"Test_gazeTracktion{self.save_counter}"
                os.makedirs(os.path.join(self.folder_path, self.save_folder_name))

                self.testing = True
                self.log(f"Начинается статическое тестироване по квадрату", "INFO", "tracker")
                self.start_testing_time = time.time()  # Запоминаем время старта
                self.circle_index = 0  # Сбрасываем индекс круга
            
            # Если нажата 'u' - Начать тестирование Moving
            elif self.key == ord('u') and not self.testingMove:

                # Определение имени для папки тестирования
                self.save_folder_name = "TestM_"+self.save_folder_name
                while os.path.exists(os.path.join(self.folder_path, self.save_folder_name)):
                    self.save_counter += 1
                    self.save_folder_name = f"TestM_gazeTracktion{self.save_counter}"
                os.makedirs(os.path.join(self.folder_path, self.save_folder_name))

                self.testingMove = True
                self.log(f"Начинается тестирование с динамическим ОУ", "INFO", "tracker")
                self.start_testing_time = time.time()  # Запоминаем время старта

            # Если нажата 'i' - Начать тестирование X
            elif self.key == ord('i') and not self.testingX:

                # Определение имени для папки тестирования
                self.save_folder_name = "TestX_"+self.save_folder_name
                while os.path.exists(os.path.join(self.folder_path, self.save_folder_name)):
                    self.save_counter += 1
                    self.save_folder_name = f"TestX_gazeTracktion{self.save_counter}"
                os.makedirs(os.path.join(self.folder_path, self.save_folder_name))

                self.testingX = True
                self.log(f"Начинается статическое тестироване по кресту", "INFO", "tracker")
                self.start_testing_time = time.time()  # Запоминаем время старта
                self.circle_index = 0  # Сбрасываем индекс круга


            # БЛОК РАБОТЫ ТЕСТИРОВАНИЯ 
            # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

            if self.testing:
                self.static_testing_1()
            elif self.testingX:
                self.static_testing_2()
            elif self.testingMove:
                self.moving_testing()
            elif self.picture_test and self.calibrated:
                self.show_picture()

            # Если нажата 'q' - Завершить работу
            if self.key == ord('q'):  
                self.log(f"Трекер завершает работу", "SUCCESS", "tracker")
                break

            # Отображение фрейма
            if (self.picture_test and (self.pic_frame is not None)):
                cv2.imshow('Eye tracker', self.pic_frame)
            else:
                cv2.imshow('Eye tracker', self.frame)

        self.cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    tracker = EyeTracker()
    tracker.start()