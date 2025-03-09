import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tracker import EyeTracker
from charts import Charts
import cv2
import screeninfo
import platform
import os
import sys
import colorama
import datetime

class EyeTrackerApp:
    
    # INIT
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __init__(self, root):
        
        self.log("Приложение трекера взгляда запускается", "INFO", "GUI")

        # Корень приложения
        self.root = root

        # Устанавливаем иконку в заголовке
        self.root.iconbitmap("C:/trackerApp/icon.ico")  

        self.icon_png_path = "C:/trackerApp/icon.png"
        
        # Устанавливаем иконку для панели задач (формат .png)
        icon = Image.open(self.icon_png_path)  # Загружаем PNG-иконку
        icon = ImageTk.PhotoImage(icon)
        self.root.wm_iconphoto(True, icon)  # Устанавливаем в панели задач

        # Определение системы
        self.system_name = platform.system() # Windows/Linux/Darwin(MacOS)

        # Флаг проведения испытаний
        self.picture_test = None

        # Определяем путь к папке испытаний "test" в текущей директории
        folder_path = os.path.join(os.getcwd(), "tests")

        # Проверяем, существует ли папка для записи результатов испытаний
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)  # Создаем папку, если её нет
            self.log(f"Папка 'tests' создана: {folder_path}", "INFO", "GUI")
        else:
            self.log(f"Папка 'tests' уже существует: {folder_path}", "INFO", "GUI")
        
        # путь до папки с испытаниями
        self.folder_path = tk.StringVar(value=folder_path)
        # путь до папки конкретного испытания
        self.test_folder_path = tk.StringVar(value="путь не выбран")
        # путь до изображения для испытаний
        self.file_path = tk.StringVar(value="файл не выбран")

        # модуль построения графиков
        self.charts = Charts()

        colorama.init()  # Инициализируем colorama

        # Запуск главного меню приложения
        self.main_menu_window()
        
    # ГЛАВНОЕ ОКНО
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def main_menu_window(self):
        self.root.title("Система отслеживания взгляда")
        self.root.protocol("WM_DELETE_WINDOW", self.close_application)
        # Устанавливаем размер окна
        window_width = 350
        window_height = 370
        # Получаем размеры экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Рассчитываем координаты верхнего левого угла для центрирования
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        # Устанавливаем положение окна
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.picture_test = False
        self.file_path.set("файл не выбран")
        
        # Главное меню
        self.main_menu_frame = tk.Frame(self.root)

        # Загрузка изображения иконки
        img = Image.open(self.icon_png_path)
        img = img.resize((88, 88))  # Можно изменить размер иконки
        self.icon_image = ImageTk.PhotoImage(img)  # Храним в self, чтобы не удалялось

        # Метка с иконкой
        self.icon_label = tk.Label(self.main_menu_frame, image=self.icon_image)
        self.icon_label.pack()
        
        # Заголовок по центру
        self.title_label = tk.Label(self.main_menu_frame, text="Главное меню трэкера", font=("Helvetica", 18))
        self.title_label.pack(pady=20)

        # РАЗДЕЛИТЕЛЬ
        self.line = tk.Canvas(self.main_menu_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line.pack(fill="x", padx=5)
        self.line.create_line(0, 1, 10000, 1, fill="black")

        # Кнопки главного меню
        self.start_button = tk.Button(self.main_menu_frame, text="Испытать трекер", command=self.test_tracker_window)
        self.start_button.pack(pady=5, fill="x")

        self.test_button = tk.Button(self.main_menu_frame, text="Применить трекер", command=self.apply_tracker_window)
        self.test_button.pack(pady=5, fill="x")

        self.make_charts_button = tk.Button(self.main_menu_frame, text="Графики", command=self.make_charts_window)
        self.make_charts_button.pack(pady=5, fill="x")

        # РАЗДЕЛИТЕЛЬ
        self.line = tk.Canvas(self.main_menu_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line.pack(fill="x", padx=5)
        self.line.create_line(0, 1, 10000, 1, fill="black")

        self.exit_button = tk.Button(self.main_menu_frame, text="Завершить работу", command=self.close_application)
        self.exit_button.pack(pady=10)

        # Изначально отображаем главное меню
        self.main_menu_frame.pack(padx=25, pady=(25, 25), fill='x', expand=False)
        self.log("GUI запущен", "INFO", "GUI")


    # ОКНО ЗАПУСКА ТРЕКЕРА
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def test_tracker_window(self):

        # Скрываем первое окно
        self.root.withdraw()
        self.first_check_cam = False

        # Создаем второе окно
        self.second_window = tk.Toplevel()
        # self.second_window.overrideredirect(True)
        # Привязываем закрытие окна к той же функции
        self.second_window.protocol("WM_DELETE_WINDOW", self.close_second_window)
        self.second_window.title("Конфигурация запуска трекера")

        # Получаем размеры экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Размеры окна
        window_width = 550
        window_height = 840

        # Рассчитываем координаты верхнего левого угла для центрирования
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        # Устанавливаем положение окна
        self.second_window.geometry(f"{window_width}x{window_height}+{x}+{y-50}")

        # Меню настройки Трекера (основной фрейм)
        self.test_tracker_frame = tk.Frame(self.second_window)
        
        # Заголовок по центру
        self.configure_title_label = tk.Label(self.test_tracker_frame, text="Выберите конфигурацию запуска трекера", font=("Helvetica", 18))
        self.configure_title_label.pack(pady=20)

        # РАЗДЕЛИТЕЛЬ
        self.line1 = tk.Canvas(self.test_tracker_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line1.pack(fill="x", padx=2)
        self.line1.create_line(0, 1, 10000, 1, fill="black")

        # Лейбл для выпадающего списка доступных камер
        self.camera_label = tk.Label(self.test_tracker_frame, text="Порт камеры (0-2 или др.):")
        self.camera_label.pack(anchor="w", pady=(10, 2))  

        available_cameras = [0,1,2]

        # Создаем выпадающий список доступных камер
        self.cameraslist = ttk.Combobox(self.test_tracker_frame, values=available_cameras)
        self.cameraslist.pack(pady=2, fill="x")
        # Устанавливаем значение по умолчанию
        self.cameraslist.set(available_cameras[0])

        if self.picture_test == True:
            self.resolutions, img_shape = self.calculate_resized_sizes()
            # Лейбл для выпадающего списка доступных разрешений окна трекера
            self.camera_label = tk.Label(self.test_tracker_frame, text=f"Разрешение окна (90%, 80% и 50% от монитора) (ориг. изображение {img_shape[0]}x{img_shape[1]}):")
            self.camera_label.pack(anchor="w", pady=2)  

            # Создаем выпадающий список разрешений
            self.reslist = ttk.Combobox(self.test_tracker_frame, values=self.resolutions, state="readonly")
            self.reslist.pack(pady=2, fill="x")
            # Устанавливаем значение по умолчанию
            self.reslist.set(self.resolutions[0])

        else:
            # Лейбл для выпадающего списка доступных разрешений окна трекера
            self.camera_label = tk.Label(self.test_tracker_frame, text="Разрешение окна:")
            self.camera_label.pack(anchor="w", pady=2)  

            self.resolutions = [
                "1280x720", "1920x1080", "2560x1440", "3840x2160",  # 16:9
                "640x480", "800x600", "1280x960"  # 4:3
            ]

            # Создаем выпадающий список разрешений
            self.reslist = ttk.Combobox(self.test_tracker_frame, values=self.resolutions, state="readonly")
            self.reslist.pack(pady=2, fill="x")
            # Устанавливаем значение по умолчанию
            self.reslist.set(self.resolutions[0])

        # Логические переменные для галочек-тумблеров
        self.fixation = tk.BooleanVar(value=False)
        self.blink = tk.BooleanVar(value=False)

        # Авто включение Direct Show для быстрого доступа к камере
        if self.system_name == "Windows":
            self.fast = tk.BooleanVar(value=True)
        else:
            self.fast = tk.BooleanVar(value=False)

        # Создаем галочки для регистрации фиксаций и морганий 
        self.fixCheck = tk.Checkbutton(self.test_tracker_frame, text="Отслеживать фиксации взгляда", variable=self.fixation)
        self.fixCheck.pack(anchor="w", pady=2)
        self.blinkCheck = tk.Checkbutton(self.test_tracker_frame, text="Отслеживать моргания", variable=self.blink)
        self.blinkCheck.pack(anchor="w", pady=2)

        # Галочка для запуска в режиме DirectShow
        self.fastCheck = tk.Checkbutton(self.test_tracker_frame, text="Режим DirectShow (быстрое подключение, низкая производительность)", variable=self.fast)
        self.fastCheck.pack(anchor="w", pady=(2,2))

        # Настройка разрешения 
        self.set_res = tk.BooleanVar(value=False)

        # Настройка разрешения (галка)
        self.set_resCheck = tk.Checkbutton(self.test_tracker_frame, text="Настроить разрешение камеры:", variable=self.set_res, command=self.toggle_res)
        self.set_resCheck.pack(anchor="w", pady=2)

        # Лейбл для выпадающего списка пороговых значений сглаживания МА
        self.set_res_label = tk.Label(self.test_tracker_frame, text="Доступные для казанной камеры разрешения:")
        self.set_res_label.pack(anchor="w", pady=2, padx=20) 
        self.supported_resolutions = ["не известно"]
        self.default_resolution = "не известно"
        # Создаем выпадающий список пороговых коэффициентов
        self.set_reslist = ttk.Combobox(self.test_tracker_frame, values=self.supported_resolutions)
        self.set_reslist.pack(pady=(2,10), padx=20, fill="x")
        # Устанавливаем значение по умолчанию
        self.set_reslist.set(self.supported_resolutions[self.supported_resolutions.index(self.default_resolution)])
        self.set_reslist.configure(state=tk.DISABLED)

        # Если не Windows, блокируем тумблер
        if self.system_name != "Windows":
            self.fastCheck.configure(state=tk.DISABLED)

        # РАЗДЕЛИТЕЛЬ
        self.line1 = tk.Canvas(self.test_tracker_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line1.pack(fill="x", padx=2)
        self.line1.create_line(0, 1, 10000, 1, fill="black")

        # Лейбл для выпадающего списка времени испытаний изображений
        self.time_label = tk.Label(self.test_tracker_frame, text="Время проведения испытания (сек.):")
        self.time_label.pack(anchor="w", pady=(10,2)) 

        # Доступные тайминги
        timings = [5,10,15,20,25,30,40,50,60,120]

        # Создаем выпадающий список таймингов
        self.timelist = ttk.Combobox(self.test_tracker_frame, values=timings)
        self.timelist.pack(pady=2, fill="x")
        # Устанавливаем значение по умолчанию
        self.timelist.set(timings[0])

        # Логическая переменная для галочки-тумблера настройки сглаживания МА
        self.ma_smooth = tk.BooleanVar(value=False)

        # Создаем галочку для МА 
        self.ma_smoothCheck = tk.Checkbutton(self.test_tracker_frame, text="Настроить MA сглаживание для координат зоны взгляда", variable=self.ma_smooth, command=self.toggle_smooth)
        self.ma_smoothCheck.pack(anchor="w", pady=2)

        # Лейбл для выпадающего списка пороговых значений сглаживания МА
        self.ma_label = tk.Label(self.test_tracker_frame, text="Значение порогового коэффициента сброса сглаживания для MA:")
        self.ma_label.pack(anchor="w", pady=2, padx=20) 

        # Доступные значения порогового коэффициента
        ma_koefs = [0.45,0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.85]

        # Создаем выпадающий список пороговых коэффициентов
        self.malist = ttk.Combobox(self.test_tracker_frame, values=ma_koefs)
        self.malist.pack(pady=2, padx=20, fill="x")
        # Устанавливаем значение по умолчанию
        self.malist.set(ma_koefs[4])
        self.malist.configure(state=tk.DISABLED)

        # Лейбл для выпадающего списка ширины окна МА
        self.ma_width_label = tk.Label(self.test_tracker_frame, text="Ширина скользящего окна:")
        self.ma_width_label.pack(anchor="w", pady=2, padx=20) 

        # Доступная ширина окна МА
        ma_width = [2,3,4,5,6,7,8,9]

        # Создаем выпадающий список ширины окна МА
        self.maWidthlist = ttk.Combobox(self.test_tracker_frame, values=ma_width)
        self.maWidthlist.pack(pady=2, padx=20, fill="x")
        # Устанавливаем значение по умолчанию
        self.maWidthlist.set(ma_width[3])
        self.maWidthlist.configure(state=tk.DISABLED)

        # Логическая переменна для галочки-тумблера для настройки Экспоненциального сглаживания
        self.exp_smooth = tk.BooleanVar(value=False)

        # Галочка для экспоненциального сглаживания
        self.exp_smoothCheck = tk.Checkbutton(self.test_tracker_frame, text="Настроить EXP сглаживание для перемещения зоны взгляда", variable=self.exp_smooth, command=self.toggle_smooth)
        self.exp_smoothCheck.pack(anchor="w", pady=2)

        # Лейбл для выпадающего списка коэффициентов экспонециального сглаживания
        self.exp_label = tk.Label(self.test_tracker_frame, text="Значение коэффициента сглаживания для EXP:")
        self.exp_label.pack(anchor="w", pady=2, padx=20) 

        # Достыпные значения для коэфициента сглаживания
        exp_koef = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]

        # Создаем выпадающий список коэфициентов сглаживания
        self.explist = ttk.Combobox(self.test_tracker_frame, values=exp_koef)
        self.explist.pack(pady=(2,10), padx=20, fill="x")
        # Устанавливаем значение по умолчанию
        self.explist.set(exp_koef[4])
        self.explist.configure(state=tk.DISABLED)

        # РАЗДЕЛИТЕЛЬ
        self.line1 = tk.Canvas(self.test_tracker_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line1.pack(fill="x", padx=2)
        self.line1.create_line(0, 1, 10000, 1, fill="black")

        # Логическая переменная для галочки-тумблера включения-отключения графиков (Общая)
        self.make_charts = tk.BooleanVar(value=True)

        # Создаем галочку для графиков (Общая) 
        self.chartsCheck = tk.Checkbutton(self.test_tracker_frame, text="Построить графики", variable=self.make_charts, command=self.toggle_fields)
        self.chartsCheck.pack(anchor="w", pady=2)
        
        # Логические переменные для галочек-тумблеров включения-отключения графиков (Частные)
        self.make_scatter = tk.BooleanVar(value=True)
        self.make_heatmap = tk.BooleanVar(value=True)

        # Создаем галочки для графиков (Частные) 
        self.scatterCheck = tk.Checkbutton(self.test_tracker_frame, text="Построить диаграмму рассеивания", variable=self.make_scatter)
        self.scatterCheck.pack(anchor="w", pady=2, padx=20)
        self.heatmapCheck = tk.Checkbutton(self.test_tracker_frame, text="Построить тепловую карту", variable=self.make_heatmap)
        self.heatmapCheck.pack(anchor="w", pady=(2,10), padx=20)

        # РАЗДЕЛИТЕЛЬ
        self.line1 = tk.Canvas(self.test_tracker_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line1.pack(fill="x", padx=2)
        self.line1.create_line(0, 1, 10000, 1, fill="black")

        # Блокировка некоторых тумблеров в случае пробного запуска трекера 
        if self.picture_test == False:
            self.make_charts.set(False)
            self.make_scatter.set(False)
            self.make_heatmap.set(False)
            self.chartsCheck.configure(state=tk.DISABLED)
            self.scatterCheck.configure(state=tk.DISABLED)
            self.heatmapCheck.configure(state=tk.DISABLED)
            self.timelist.configure(state=tk.DISABLED)
            self.ma_smoothCheck.configure(state=tk.DISABLED)
            self.exp_smoothCheck.configure(state=tk.DISABLED)
        
        # Создаём стиль для кнопки
        style = ttk.Style()
        style.configure("Custom.TButton", background="green")
        start_button = ttk.Button(self.test_tracker_frame, text="Запустить трекер", style="Custom.TButton", command=self.start_tracker)
        start_button.pack(pady=(10,2), fill="x")

        # Кнопка запуска трекера
        # self.start_button = tk.Button(self.test_tracker_frame, text="Запустить трекер", command=self.start_tracker)
        # self.start_button.pack(pady=(10,2), fill="x")

        # Фрейм для нижних кнопок навигации
        self.test_tracker_frame_bottom = tk.Frame(self.second_window)
        
        # Кнопка для возврата на главное меню
        self.back_button = tk.Button(self.test_tracker_frame_bottom, text="Назад в главное меню", command=self.close_second_window)
        # Кнопка для открытия окна справки
        self.help_button = tk.Button(self.test_tracker_frame_bottom, text="Открыть справку", command=self.open_help_window)

        self.back_button.pack(side="left", padx=20, expand=True)
        self.help_button.pack(side="right", padx=20, expand=True)

        self.test_tracker_frame.pack(padx=25, pady=(10,8), fill='x', expand=False)
        self.test_tracker_frame_bottom.pack(padx=25, pady=(2, 15), fill='x', expand=False)
    

    def get_camera_resolutions(self):

        resolutions = [
            (3840, 2160), (2560, 1440), (1920, 1080), (1600, 900), (1280, 720), 
            (1024, 576), (800, 600), (640, 480), (320, 240)]
        
        cap = cv2.VideoCapture(int(self.cameraslist.get()), cv2.CAP_DSHOW)

        if not cap.isOpened():
            messagebox.showwarning("Предупреждение", f"Выбранной камеры не существует, попробуйте другой индекс")
            self.log(f"Ошибка: Не удалось открыть веб-камеру!", "ERROR", "GUI")
            return

        # Получаем разрешение по умолчанию
        default_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        default_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        default_resolution = f"{default_width}x{default_height}"

        supported_resolutions = []

        for width, height in resolutions:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if (actual_width, actual_height) == (width, height):
                supported_resolutions.append(f"{width}x{height}")

        cap.release()

        # Сортировка по убыванию (размер изображения в пикселях)
        supported_resolutions.sort(key=lambda res: int(res.split('x')[0]) * int(res.split('x')[1]), reverse=True)

        self.log(f"Разрешение по умолчанию: {default_resolution}", "INFO", "GUI")
        self.log(f"Доступные разрешения: {supported_resolutions}", "INFO", "GUI")

        self.default_resolution = default_resolution
        self.supported_resolutions = supported_resolutions

        self.first_check_cam = True
    

    def calculate_resized_sizes(self):
        # Загружаем изображение
        image = cv2.imread(self.file_path.get())
        if image is None:
            raise ValueError("Ошибка: не удалось загрузить изображение!")

        img_h, img_w, _ = image.shape  # Определяем размеры изображения

        # Получаем размеры экрана пользователя
        screen = screeninfo.get_monitors()[0]  # Берем первый экран
        screen_w, screen_h = screen.width, screen.height

        # Определяем, что больше: ширина или высота
        img_is_wider = img_w > img_h  # True, если ширина больше

        # Берем соответствующее измерение экрана
        screen_max = screen_w if img_is_wider else screen_h

        # Вычисляем три размера с уменьшением
        size_factors = [0.9, 0.8, 0.5]  # 10%, 20% и 50% уменьшение
        sizes = {}

        for i, factor in enumerate(size_factors, 1):
            new_main = int(screen_max * factor)  # Новая ширина или высота (в зависимости от ориентации)
            aspect_ratio = img_h / img_w if img_is_wider else img_w / img_h  # Соотношение сторон

            if img_is_wider:
                new_w = new_main
                new_h = int(new_w * aspect_ratio)
            else:
                new_h = new_main
                new_w = int(new_h * aspect_ratio)

            sizes[f"size_{i}"] = {"width": new_w, "height": new_h}

        return [f"{size['width']}x{size['height']}" for size in sizes.values()], (img_w, img_h)

    
    # ОКНО НАСТРОЙКИ ПУТЕЙ 
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def apply_tracker_window(self):

        # Скрываем первое окно
        self.root.withdraw()

        # Создаем второе окно
        self.third_window = tk.Toplevel()
        # self.third_window.overrideredirect(True)
        self.third_window.protocol("WM_DELETE_WINDOW", self.close_third_window)
        self.third_window.title("Применение трекера")

        # Получаем размеры экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Размеры окна
        window_width = 550
        window_height = 380

        # Рассчитываем координаты верхнего левого угла для центрирования
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        self.picture_test = False
        self.file_path.set("файл не выбран")

        # Устанавливаем положение окна
        self.third_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Меню настройки Трекера
        self.apply_tracker_frame = tk.Frame(self.third_window)
        
        # Заголовок по центру
        self.configure_title_label = tk.Label(self.apply_tracker_frame, text="Выбор каталога и файлов", font=("Helvetica", 18))
        self.configure_title_label.pack(pady=20)

        # РАЗДЕЛИТЕЛЬ
        self.line1 = tk.Canvas(self.apply_tracker_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line1.pack(fill="x", padx=2)
        self.line1.create_line(0, 1, 10000, 1, fill="black")
        
        # Лейба для кнопки выбора пути сохранения результатов испытаний
        self.save_path_label = tk.Label(self.apply_tracker_frame, text="Выбирите папку для сохранения отслеживания:")
        self.save_path_label.pack(anchor="w", pady=(10, 2))

        # Кнопка выбора пути сохранения результатов испытаний
        self.save_button = tk.Button(self.apply_tracker_frame, text="Обзор каталогов", command=self.choose_folder)
        self.save_button.pack(anchor="w", pady=2)

        # Лейба для кнопки выбора пути изображения для испытаний
        self.file_path_label = tk.Label(self.apply_tracker_frame, text="Выберите изображение (*.jpg, *.png):")
        self.file_path_label.pack(anchor="w", pady=(10, 2))

        # Кнопка выбора пути изображения для испытаний
        self.img_button = tk.Button(self.apply_tracker_frame, text="Выбрать изображение", command=self.choose_file)
        self.img_button.pack(anchor="w", pady=(2, 10))

        # РАЗДЕЛИТЕЛЬ
        self.line1 = tk.Canvas(self.apply_tracker_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line1.pack(fill="x", padx=2)
        self.line1.create_line(0, 1, 10000, 1, fill="black")

        # Метка для отображения пути к папке
        self.folder_path_lable = tk.Label(self.apply_tracker_frame, textvariable=self.folder_path, wraplength=400, justify="left")
        self.folder_path_lable.pack(anchor="w", pady=(10,2))

        # Метка для отображения пути к файлу
        self.img_path_label = tk.Label(self.apply_tracker_frame, textvariable=self.file_path, wraplength=400, justify="left")
        self.img_path_label.pack(anchor="w", pady=(2,10))

        # РАЗДЕЛИТЕЛЬ
        self.line1 = tk.Canvas(self.apply_tracker_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line1.pack(fill="x", padx=2)
        self.line1.create_line(0, 1, 10000, 1, fill="black")

        # Фрейм для нижних кнопок навигации
        self.apply_tracker_frame_bottom = tk.Frame(self.third_window)

        # Кнопка для возврата на главный экран
        self.back_button = tk.Button(self.apply_tracker_frame_bottom, text="Назад в главное меню", command=self.close_third_window)
        # Кнопка для открытия окна справки
        self.help_button = tk.Button(self.apply_tracker_frame_bottom, text="Открыть справку", command=self.open_help_window)
        # Кнопка для перехода к окну настройки запуска трекера (ко второму окну)
        self.forward_button = tk.Button(self.apply_tracker_frame_bottom, text="Далее", command=self.check_path)

        self.back_button.pack(side="left", padx=(0,20), expand=False)
        self.help_button.pack(side="left", padx=(20,20), expand=False)
        self.forward_button.pack(side="right", padx=(20, 0), expand=False)

        self.apply_tracker_frame.pack(padx=25, pady=(10, 10), fill='x', expand=False)
        self.apply_tracker_frame_bottom.pack(padx=25, pady=(10, 25))
    

    # ОКНО построения графиков
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def make_charts_window(self):

        # Скрываем первое окно
        self.root.withdraw()

        # Создаем второе окно
        self.chart_window = tk.Toplevel()
        self.chart_window.protocol("WM_DELETE_WINDOW", self.close_chart_window)
        self.chart_window.title("Построение графиков")

        # Получаем размеры экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Размеры окна
        window_width = 550
        window_height = 370

        # Рассчитываем координаты верхнего левого угла для центрирования
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        self.picture_test = False
        self.file_path.set("файл не выбран")

        # Устанавливаем положение окна
        self.chart_window.geometry(f"{window_width}x{window_height}+{x}+{y-100}")

        # Меню настройки Трекера
        self.chart_window_frame = tk.Frame(self.chart_window)
        
        # Заголовок по центру
        self.configure_title_label = tk.Label(self.chart_window_frame, text="Конфигуратор построения графиков", font=("Helvetica", 18))
        self.configure_title_label.pack(pady=20)

        # РАЗДЕЛИТЕЛЬ
        self.line1 = tk.Canvas(self.chart_window_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line1.pack(fill="x", padx=2)
        self.line1.create_line(0, 1, 10000, 1, fill="black")
        
        # Лейба для кнопки выбора пути папки испытания
        self.test_path_label = tk.Label(self.chart_window_frame, text="Выбирите папку испытания:")
        self.test_path_label.pack(anchor="w", pady=(10, 2))

        # Кнопка выбора пути пакпи испытания
        self.test_path_button = tk.Button(self.chart_window_frame, text="Обзор каталогов", command=self.choose_test_folder)
        self.test_path_button.pack(anchor="w", pady=2)

        # # Лейба для кнопки выбора пути изображения для испытаний
        # self.file_path_label = tk.Label(self.apply_tracker_frame, text="Выберите изображение:")
        # self.file_path_label.pack(anchor="w", pady=(10, 2))

        # # Кнопка выбора пути изображения для испытаний
        # self.img_button = tk.Button(self.apply_tracker_frame, text="Выбрать изображение", command=self.choose_file)
        # self.img_button.pack(anchor="w", pady=(2, 10))

        # Метка для отображения пути к папке
        self.folder_path_lable = tk.Label(self.chart_window_frame, textvariable=self.test_folder_path, wraplength=400, justify="left")
        self.folder_path_lable.pack(anchor="w", pady=(10,2))

        # РАЗДЕЛИТЕЛЬ
        self.line1 = tk.Canvas(self.chart_window_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line1.pack(fill="x", padx=2)
        self.line1.create_line(0, 1, 10000, 1, fill="black")

        # Переменная для хранения выбранного варианта
        self.selected_chart = tk.IntVar(value=1)  # Значение по умолчанию (можно 0, 1, 2)

        # Радиокнопки
        ttk.Radiobutton(self.chart_window_frame, text="Диаграмма рассеивания", variable=self.selected_chart, value=1, command=self.update_chart_ui).pack(anchor="w", pady=2)
        ttk.Radiobutton(self.chart_window_frame, text="Тепловая карта", variable=self.selected_chart, value=2, command=self.update_chart_ui).pack(anchor="w", pady=2)
        ttk.Radiobutton(self.chart_window_frame, text="Гистограмма радиуса зоны взгляда", variable=self.selected_chart, value=3, command=self.update_chart_ui).pack(anchor="w", pady=2)


        # РАЗДЕЛИТЕЛЬ
        self.line1 = tk.Canvas(self.chart_window_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line1.pack(fill="x", padx=2)
        self.line1.create_line(0, 1, 10000, 1, fill="black")

        # Фрейм для динамических элементов
        self.dynamic_frame = ttk.Frame(self.chart_window)
        self.update_chart_ui()


        # Фрейм для нижних кнопок навигации
        self.chart_window_frame_bottom = tk.Frame(self.chart_window)

        # Кнопка для возврата на главный экран
        self.back_button = tk.Button(self.chart_window_frame_bottom, text="Назад в главное меню", command=self.close_chart_window)
        # Кнопка для перехода к окну настройки запуска трекера (ко второму окну)
        self.chart_button = tk.Button(self.chart_window_frame_bottom, text="Получить график", command=self.check_chart_path)

        self.back_button.pack(side="left", padx=(0,20), expand=False)
        self.chart_button.pack(side="right", padx=(20, 0), expand=False)
        self.chart_button.configure(state=tk.DISABLED)

        self.chart_window_frame.pack(padx=25, pady=(10, 2), fill='x', expand=False)
        self.dynamic_frame.pack(padx=25, fill='x', expand=False)
        self.chart_window_frame_bottom.pack(padx=25, pady=(10, 25))
        

    def update_chart_ui(self):
        """Обновляет интерфейс в зависимости от выбранной опции."""
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()  # Удаляем все элементы перед обновлением

        if self.test_folder_path.get() != "путь не выбран":

            found = any(f.startswith("gaze") and f.endswith(".txt") for f in os.listdir(self.test_folder_path.get()))

            # Вывод результата
            if found:
                
                self.chart_button.configure(state=tk.NORMAL)
                self.log(f"В папке обнаружены данные взгляда (gazeX.txt)", "INFO", "GUI")

                if self.selected_chart.get() == 1:

                    # Переменные для надписей графика
                    self.entry_title = tk.StringVar(value="Визуализация данных взгляда пользователя на изображение")
                    self.entry_xlable = tk.StringVar(value="Х координаты по ширине")
                    self.entry_ylable = tk.StringVar(value="Y координаты по высоте")

                    ttk.Label(self.dynamic_frame, text="Заголовок для диаграммы распределения:").pack(anchor="w", pady=2)
                    ttk.Entry(self.dynamic_frame, textvariable=self.entry_title).pack(anchor="w", pady=(2,5), fill="x")

                    ttk.Label(self.dynamic_frame, text="Наименование оси абсцисс:").pack(anchor="w", pady=2)
                    ttk.Entry(self.dynamic_frame, textvariable=self.entry_xlable).pack(anchor="w", pady=(2,5), fill="x")

                    ttk.Label(self.dynamic_frame, text="Наименование оси ординат:").pack(anchor="w", pady=2)
                    ttk.Entry(self.dynamic_frame, textvariable=self.entry_ylable).pack(anchor="w", pady=(2,10), fill="x")

                    # Проверяем файлы в указанной папке
                    found = any(f.startswith("fix") and f.endswith(".txt") for f in os.listdir(self.test_folder_path.get()))

                    # Вывод результата
                    if found:
                        # Логическая переменна для галочки-тумблера для фиксаций
                        self.fix_chart = tk.BooleanVar(value=False)

                        # Галочка для экспоненциального сглаживания
                        self.fix_chartCheck = tk.Checkbutton(self.dynamic_frame, text="Построить график с фиксациями взгляда", variable=self.fix_chart)
                        self.fix_chartCheck.pack(anchor="w", pady=2)

                    # Лейбл для выпадающего списка непрозрачности фона
                    self.alpha_bg_label = tk.Label(self.dynamic_frame, text="Непрозрачность фонового изображения:")
                    self.alpha_bg_label.pack(anchor="w", pady=2) 

                    # Доступные непрозрачности
                    alpha_bg = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]

                    # Создаем выпадающий список непрозрачностей взгляда
                    self.alpha_bg_list = ttk.Combobox(self.dynamic_frame, values=alpha_bg)
                    self.alpha_bg_list.pack(pady=2, fill="x")
                    # Устанавливаем значение по умолчанию
                    self.alpha_bg_list.set(alpha_bg[1])

                    # Лейбл для выпадающего списка непрозрачностей взгляда
                    self.alpha_gaze_label = tk.Label(self.dynamic_frame, text="Непрозрачность точек взгляда:")
                    self.alpha_gaze_label.pack(anchor="w", pady=2) 

                    # Доступные непрозрачности взгляда
                    alpha_gaze = [0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.5]

                    # Создаем выпадающий список непрозрачностей взгляда
                    self.alpha_gaze_list = ttk.Combobox(self.dynamic_frame, values=alpha_gaze)
                    self.alpha_gaze_list.pack(pady=(2,10), fill="x")
                    # Устанавливаем значение по умолчанию
                    self.alpha_gaze_list.set(alpha_gaze[0])
                    

                elif self.selected_chart.get() == 2:
                    # Переменные для надписей графика
                    self.entry_title = tk.StringVar(value="Тепловая карта взгляда пользователя на изображение")
                    self.entry_xlable = tk.StringVar(value="Х координаты по ширине")
                    self.entry_ylable = tk.StringVar(value="Y координаты по высоте")

                    ttk.Label(self.dynamic_frame, text="Заголовок для тепловой карты:").pack(anchor="w", pady=2)
                    ttk.Entry(self.dynamic_frame, textvariable=self.entry_title).pack(anchor="w", pady=(2,5), fill="x")

                    ttk.Label(self.dynamic_frame, text="Наименование оси абсцисс:").pack(anchor="w", pady=2)
                    ttk.Entry(self.dynamic_frame, textvariable=self.entry_xlable).pack(anchor="w", pady=(2,5), fill="x")

                    ttk.Label(self.dynamic_frame, text="Наименование оси ординат:").pack(anchor="w", pady=2)
                    ttk.Entry(self.dynamic_frame, textvariable=self.entry_ylable).pack(anchor="w", pady=(2,10), fill="x")

                elif self.selected_chart.get() == 3:
                    # Переменные для надписей графика
                    self.entry_title = tk.StringVar(value="Распределение радиусов точек взгляда")
                    self.entry_xlable = tk.StringVar(value="Радиус (пиксели)")
                    self.entry_ylable = tk.StringVar(value="Частота")

                    ttk.Label(self.dynamic_frame, text="Заголовок для гистограммы радиусов:").pack(anchor="w", pady=2)
                    ttk.Entry(self.dynamic_frame, textvariable=self.entry_title).pack(anchor="w", pady=(2,5), fill="x")

                    ttk.Label(self.dynamic_frame, text="Наименование оси абсцисс:").pack(anchor="w", pady=2)
                    ttk.Entry(self.dynamic_frame, textvariable=self.entry_xlable).pack(anchor="w", pady=(2,5), fill="x")

                    ttk.Label(self.dynamic_frame, text="Наименование оси ординат:").pack(anchor="w", pady=2)
                    ttk.Entry(self.dynamic_frame, textvariable=self.entry_ylable).pack(anchor="w", pady=(2,10), fill="x")
            else:
                self.log(f"Данные взгляда в папке отсутствуют", "WARNING", "GUI")
                ttk.Label(self.dynamic_frame, text="Данные взгляда в папке отсутствуют").pack(anchor="w", pady=5)
        else:
            ttk.Label(self.dynamic_frame, text="Виберете каталог с испытанием").pack(anchor="w", pady=5)
        
        # РАЗДЕЛИТЕЛЬ
        self.line1 = tk.Canvas(self.dynamic_frame, height=2, bd=0, highlightthickness=0, relief="flat")
        self.line1.pack(fill="x", padx=2)
        self.line1.create_line(0, 1, 10000, 1, fill="black")
        

        min_height = 370  # Минимальная высота окна

        # Обновляем геометрию окна после изменения содержимого
        self.chart_window.update_idletasks()  # Обновляем внутренние размеры окна
        content_height = self.chart_window.winfo_reqheight()
        
        # Дополнительно прибавляем отступы (pady) к общей высоте
        extra_padding = 0
        for widget in self.chart_window.winfo_children():
            if widget.winfo_ismapped():  # Проверяем, упакован ли виджет
                pack_info = widget.pack_info()
                pady = pack_info.get("pady", 0)
                
                if isinstance(pady, tuple):
                    # Если pady вернул кортеж, извлекаем его первый элемент
                    pady = pady[0]
                
                extra_padding += int(pady) * 2  # Учитываем верхний и нижний pady

        # Итоговая высота с учетом отступов
        new_height = content_height + extra_padding
        self.chart_window.geometry(f"{550}x{max(new_height, min_height)}")
    

    # Проверка пути перед конфигурацией трекера
    def check_chart_path(self):
        
        path = self.test_folder_path.get()
        title = self.entry_title.get()
        xlable = self.entry_xlable.get()
        ylable = self.entry_ylable.get()
        width, height = 0, 0
        try:
            with open(path+"/res.txt", "r") as file:
                content = file.read().strip()
                # Преобразуем строку в кортеж
                width, height = map(int, content.strip('()').split(','))
        except FileNotFoundError:
            self.log(f"Файл res.txt не найден", "WARNING", "GUI")
            return

        if self.selected_chart.get() == 1:
            try:
                fixations = self.fix_chart.get()
            except Exception as e:
                fixations = False
            alpha_bg = float(self.alpha_bg_list.get())
            alpha_gaze = float(self.alpha_gaze_list.get())
            self.charts.scatter_plot_pictures(folder_path=path, width=width, height=height, fixations=fixations, alpha_bg=alpha_bg, alpha_gaze=alpha_gaze, title=title, xlable=xlable, ylable=ylable)
        elif self.selected_chart.get() == 2:
            self.charts.heatmap_pictures(folder_path=path, width=width, height=height, title=title, xlable=xlable, ylable=ylable)
        elif self.selected_chart.get() == 3:
            self.charts.radius_hist(folder_path=path, title=title, xlable=xlable, ylable=ylable)

            



    # ОКНО СПРАВКИ
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def open_help_window(self):

        # Создаем третье окно
        self.help_window = tk.Toplevel(self.root)
        self.help_window.title("Справка по работе трекера")

        # Задаем размеры окна справки
        self.help_window.geometry("800x550")

        # Текст справки
        help_text = (            
            "Это справка по работе трекера.\n"
            "Перед началом работы трекера в окне конфигурации выбирете соответствующие настройки:\n\n"
            "1. Выберете камеру (обычно основная вебкамера находится по индексом 0, в других случая 1-3)\n\n"
            "2. Выберете разрешение окна трекера (не более разрешения экрана)\n\n"
            "Для взаимодействия с запущенным трекером необходимо переключиться на английскую развертку клавиатуры\n\n"
            "3. В начале происходит калибровка по зрачкам пользователя. Необходимо посмотреть в три красные точки на экране:\n"
            "3.1 по центру экрана,\n3.2 в левом верхнем углу окна,\n3.3 в правом нижнем углу окна;\n"
            "при фиксации взгляда на них каждый раз нажимать клавишу 'пробел'(space)\n\n"
            "4. Далее трекер входит в основной режим работы, отслеживая взгляд пользователя на экране.\n"
            "ВАЖНО - при работе трекера не отклоняйте голову от положения калибровки. В противном случае придется прохожить ее заного.\n\n"
            "5. Для завершения работы трекера нажмите 'q'\n\n"
            "*** Весь список назначенных клавишь перечислен далее:\n\n"
            "'space' - фиксация взгляда при калибровке\n"
            "'q' - завершение работы трекера взгляда\n"
            "'k' - запуск новой калибровки\n"
            "'t' - начать тестирование по квадрату\n"
            "'i' - начать тестирование по кресту\n"
            "'u' - начать тестирование с динамической целью\n\n"
            "Пожалуйста, следуйте этим шагам для корректной работы трекера."
        )

        # Метка с текстом справки
        help_label = tk.Label(self.help_window, text=help_text, justify="left", padx=10, pady=10, wraplength=800)
        help_label.pack()
    

    # Функция блокировки и разблокировки элементов
    def toggle_fields(self):

        state = tk.NORMAL if self.make_charts.get() else tk.DISABLED
        self.scatterCheck.configure(state=state)
        self.heatmapCheck.configure(state=state)


    # Функция блокировки и разблокировки элементов
    def toggle_smooth(self):

        state1 = tk.NORMAL if self.ma_smooth.get() else tk.DISABLED
        state2 = tk.NORMAL if self.exp_smooth.get() else tk.DISABLED
        self.malist.configure(state=state1)
        self.maWidthlist.configure(state=state1)
        self.explist.configure(state=state2)

    # Функция получения расширений
    def toggle_res(self):
        if self.first_check_cam == False:
            messagebox.showinfo("Информация", f"Подождите пока будут получены все возможные разрешения работы вашей камеры")
            self.get_camera_resolutions()
        state1 = tk.NORMAL if self.set_res.get() else tk.DISABLED
        self.set_reslist.configure(state=state1, values=self.supported_resolutions)
        self.set_reslist.set(self.supported_resolutions[self.supported_resolutions.index(self.default_resolution)])


    # Проверка пути перед конфигурацией трекера
    def check_path(self):

        if self.folder_path.get() == "путь не выбран":
            messagebox.showwarning("Предупреждение", "Вы не выбрали папку, в которой будет сохранен результат отслеживания")
        elif self.file_path.get() == "файл не выбран":
            messagebox.showwarning("Предупреждение", "Вы не выбрали изображение для отслеживания")
        else:
            # Закрываем второе окно
            self.third_window.destroy()
            self.picture_test = True
            self.test_tracker_window()


    # Функция закрытия окна конфигурации
    def close_second_window(self):

        # Закрываем второе окно
        self.second_window.destroy()
        # Тестирования картинки (если было) завершено
        self.picture_test = False
        # Забываем выбранный файл
        self.file_path.set("файл не выбран")
        # Возвращаем первое окно
        self.root.deiconify()
    
    
    # Функция закрытия окна конфигурации
    def close_third_window(self):
        # Закрываем второе окно
        self.third_window.destroy()
        # Возвращаем первое окно
        self.root.deiconify()

    
    # Функция закрытия окна графиков
    def close_chart_window(self):
        # Закрываем второе окно
        self.chart_window.destroy()
        self.test_folder_path.set("путь не выбран")
        # Возвращаем первое окно
        self.root.deiconify()
    

    # Выбор папки испытания
    def choose_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.folder_path.get())  # Открывает окно выбора папки
        if folder_selected:  
            self.folder_path.set(folder_selected)  # Устанавливаем путь в переменную
    
    # Выбор папки испытания
    def choose_test_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.folder_path.get())  # Открывает окно выбора папки
        if folder_selected:  
            self.test_folder_path.set(folder_selected)  # Устанавливаем путь в переменную
            self.update_chart_ui()
    
    # Выбор файла для испытания
    def choose_file(self):
        # Открывает диалоговое окно выбора файла
        file_selected = filedialog.askopenfilename(initialdir=os.getcwd())
        if file_selected:
            self.file_path.set(file_selected)  # Устанавливаем путь в метку

    
    # Запуск приложения трекера
    def start_tracker(self):

        """Запуск трекера"""
        if self.picture_test == False:
            file_path = None
        else:
            file_path = self.file_path.get()
        
        if self.set_res.get():
            cam_res = self.set_reslist.get()
        else:
            cam_res = None

        self.tracker = EyeTracker(camera=int(self.cameraslist.get()),
                                  res=self.reslist.get(),
                                  cam_res=cam_res,
                                  fixation=self.fixation.get(),
                                  blink=self.blink.get(),
                                  fast=self.fast.get(),
                                  folder_path=self.folder_path.get(),
                                  file_path=file_path,
                                  duration=int(self.timelist.get()),
                                  ma_trshhd=float(self.malist.get()),
                                  ma_width=int(self.maWidthlist.get()),
                                  exp_koef=float(self.explist.get()))
        
        self.log(f"Трекер запускается", "INFO", "GUI")
        self.tracker.start()
        self.log(f"Трекер завершил работу", "INFO", "GUI")
        data = self.tracker.callback_data()
        if self.make_charts.get() == True:
            if self.make_scatter.get() == True:
                self.log(f"Начинается построение диаграммы рассеивания данных взгляда", "INFO", "GUI")
                self.charts.scatter_plot_pictures(folder_path=self.folder_path.get()+"/"+data["folder_name"], width=data["width"], height=data["height"], fixations=self.fixation.get())
            if self.make_heatmap.get() == True:
                self.log(f"Начинается построение тепловой карты данных взгляда", "INFO", "GUI")
                self.charts.heatmap_pictures(folder_path=self.folder_path.get()+"/"+data["folder_name"], width=data["width"], height=data["height"])
            if self.make_scatter.get() == True or self.make_heatmap.get() == True:
                messagebox.showinfo("Информация", f"Графики сохранены в корневой папке испытания:\n{self.folder_path.get()}"+"/"+f"{data['folder_name']}")
        if data["tested"]:
            self.log(f"Начинается построение диаграммы рассеивания по тестовым данным", "INFO", "GUI")
            self.charts.scatter_plot_testing(folder_path=self.folder_path.get()+"/"+data["folder_name"], width=data["width"], height=data["height"], fixations=self.fixation.get())
        elif data["testedM"]:
            self.log(f"Начинается построение диаграммы рассеивания по тестовым данным", "INFO", "GUI")
            self.charts.scatter_plot_testingM(folder_path=self.folder_path.get()+"/"+data["folder_name"], width=data["width"], height=data["height"], fixations=self.fixation.get(), heatmap=True)

    
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

    # Функция для завершения приложения
    def close_application(self):
        self.root.destroy()

def main():
    root = tk.Tk()
    app = EyeTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":

    main()
