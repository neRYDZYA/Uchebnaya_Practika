# Импорт необходимых библиотек
import turtle  # Графическая библиотека для рисования
import time    # Для работы со временем
import random  # Для генерации случайных чисел
import os      # Для работы с файловой системой
import json    # Для работы с JSON-файлами
import multiprocessing  # Для запуска игры в отдельном процессе
import sys     # Для системных функций
from tkinter import *  # GUI библиотека
from tkinter import simpledialog, messagebox, ttk  # Элементы GUI
from tkinter.scrolledtext import ScrolledText  # Текстовое поле с прокруткой

# Константы
LEADERBOARD_FILE = "leaderboard.json"  # Файл для хранения рекордов

# Класс для хранения настроек игры
class GameSettings:
    def __init__(self):
        self.count = 0         # Счетчик анимации динозавра
        self.dx = 5           # Горизонтальная скорость объектов
        self.pdy = 9          # Вертикальная скорость прыжка вверх
        self.mdy = -10         # Вертикальная скорость падения
        self.randcounter = 0   # Счетчик для случайных событий
        self.cloudx = 0.1      # Скорость движения облаков
        self.score = 0         # Текущий счет
        self.distance = 31     # Дистанция столкновения
        self.game_over = False # Флаг окончания игры
        self.dy = 0            # Текущая вертикальная скорость
        self.is_jumping = False # Флаг прыжка
        self.jump_timer = 0     # Таймер прыжка
        self.jump_lock = False  # Блокировка прыжка
        self.start_time = time.time()  # Время начала игры
        self.elapsed_time = 0   # Прошедшее время игры

# Глобальные переменные
settings = GameSettings()  # Экземпляр настроек игры
win = None      # Окно игры (turtle.Screen)
dino = None     # Объект динозавра
obs1 = None     # Первое препятствие
obs2 = None     # Второе препятствие
cloud1 = None   # Первое облако
cloud2 = None   # Второе облако
dust = None     # Частицы пыли
dust2 = None    # Частицы пыли
dust3 = None    # Частицы пыли
pen = None      # Объект для отображения текста
imglst = []     # Список изображений для анимации динозавра
objimg = []     # Список изображений препятствий
username = None

def center_window(window, width, height):
    """Центрирует окно на экране"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def get_username():
    """Запрашивает и сохраняет имя игрока"""
    global username
    
    # Создаем временное окно для запроса имени
    root = Tk()
    root.withdraw()
    center_window(root, 300, 150)
    
    while True:
        username_input = simpledialog.askstring(
            "Никнейм",
            "Введите ваш никнейм (макс. 15 символов):",
            parent=root
        )
        
        # Если нажали Cancel или закрыли окно
        if username_input is None:
            username = "Игрок"
            break
            
        username_input = username_input.strip()
        
        if username_input:  # Если ввели не пустую строку
            username = username_input[:15]
            break
        else:
            retry = messagebox.askretrycancel(
                "Ошибка",
                "Никнейм не может быть пустым. Повторить ввод?"
            )
            if not retry:
                username = "Игрок"
                break
    
    root.destroy()
    return username

def save_score():
    """Сохраняет результат с гарантированным именем игрока"""
    global username
    
    # Убедимся, что имя есть
    if username is None:
        username = "Игрок"
    
    # Подготовка данных для сохранения
    new_score = {
        "name": username,
        "score": settings.score,
        "time": round(settings.elapsed_time, 2)
    }
    
    # Загрузка текущей таблицы лидеров
    try:
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                leaderboard = json.load(f)
        else:
            leaderboard = []
    except:
        leaderboard = []
    
    # Добавление нового результата
    leaderboard.append(new_score)
    
    # Сортировка и сохранение топ-10
    leaderboard.sort(key=lambda x: (-x['score'], x['time']))
    leaderboard = leaderboard[:10]
    
    # Сохранение обновленной таблицы
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(leaderboard, f, ensure_ascii=False, indent=2)

def create_turtle(shape, x, y):
    """Создает объект turtle с заданной формой и позицией"""
    t = turtle.Turtle()
    t.shape(shape)
    t.penup()
    t.hideturtle()
    t.goto(x, y)
    return t

def jump():
    """Обрабатывает прыжок динозавра"""
    ycor = dino.ycor()
    if settings.is_jumping and not settings.jump_lock and ycor <= 142:
        settings.jump_timer = 20
        settings.jump_lock = True
        settings.is_jumping = False

    if settings.jump_timer > 0:
        settings.dy = settings.pdy
        dino.sety(ycor + settings.dy)
        settings.jump_timer -= 1
    else:
        if ycor > 142:
            settings.dy = settings.mdy
            dino.sety(ycor + settings.dy)
        else:
            dino.sety(142)
            settings.dy = 0
            settings.jump_lock = False

def cloud_move(cloud):
    """Двигает облака"""
    cloudx = cloud.xcor()
    cloud.setx(cloudx - settings.cloudx)
    if cloudx < -300:
        cloudx = random.randint(350, 430)
        cloud.setx(cloudx)
    if -300 < cloudx < 300:
        cloud.showturtle()
    else:
        cloud.hideturtle()

def dust_move(dust_obj, other_dust=None):
    """Двигает частицы пыли"""
    dustx = dust_obj.xcor()
    dust_obj.setx(dustx - settings.dx)
    if dustx < -300:
        dustrx = random.randint(350, 430)
        if other_dust and dust_obj.distance(other_dust) <= 50:
            dustrx += 200
        dust_obj.setx(dustrx)
    if -300 < dustx < 300:
        dust_obj.showturtle()
    else:
        dust_obj.hideturtle()

def obstacle_move(obstacle, other_obstacle=None):
    """Двигает препятствия"""
    obsx = obstacle.xcor()
    obstacle.setx(obsx - settings.dx)
    if obsx < -300:
        obstacle.hideturtle()
        bgmg = random.choice(objimg)
        obstacle.shape(bgmg)
        obsrx = random.randint(350, 430)
        if other_obstacle and obstacle.distance(other_obstacle) <= 200:
            obsrx += 200
        obstacle.setx(obsrx)
    if -300 < obsx < 300:
        obstacle.showturtle()
    else:
        obstacle.hideturtle()

def check_collision():
    """Проверяет столкновение динозавра с препятствиями"""
    if (dino.distance(obs1) <= settings.distance or
        dino.distance(obs2) <= settings.distance):
        return True
    return False

def game_over_screen():
    """Отображает экран окончания игры"""
    settings.game_over = True
    settings.elapsed_time = time.time() - settings.start_time
    save_score()

    def open_leaderboard():
        show_leaders()

    def return_to_menu():
        # Закрываем окно turtle
        win.bye()  # Закрываем экран turtle
        over_root.destroy()  # Закрываем окно поражения
        show_menu()  # Показываем главное меню

    over_root = Tk()
    over_root.title("КОНЕЦ ИГРЫ")
    center_window(over_root, 300, 250)
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12), padding=10)

    Label(over_root, text="ПОРАЖЕНИЕ", font=("Arial", 20, "bold")).pack(pady=10)
    Label(over_root, text=f"Очки: {settings.score}", font=("Arial", 14)).pack()
    Label(over_root, text=f"Время: {round(settings.elapsed_time, 2)} c", font=("Arial", 12)).pack(pady=(0, 20))

    ttk.Button(over_root, text="Начать заново (Enter)", command=lambda: [over_root.destroy(), reset_game()]).pack(pady=5, fill=X)
    ttk.Button(over_root, text="Выход в меню", command=return_to_menu).pack(pady=5, fill=X)
    ttk.Button(over_root, text="Таблица лидеров", command=open_leaderboard).pack(pady=5, fill=X)

    over_root.mainloop()

def reset_game():
    """Сбрасывает игру в начальное состояние"""
    global settings
    settings = GameSettings()
    pen.clear()
    dino.goto(-255, 142)
    obs1.goto(420, 140)
    obs2.goto(700, 140)
    obs1.shape(obj1)
    obs2.shape(obj2)
    cloud1.goto(250, 220)
    cloud2.goto(250, 220)
    dust.goto(420, 127)
    dust2.goto(420, 127)
    dust3.goto(420, 127)
    for obj in [obs1, obs2, cloud1, cloud2, dust, dust2, dust3]:
        obj.hideturtle()
    pen.goto(175, 231)
    settings.game_over = False
    settings.start_time = time.time()
    game_loop()

def game_loop():
    """Основной игровой цикл"""
    while True:
        win.update()
        if settings.game_over:
            time.sleep(0.1)
            continue
        settings.randcounter += 1
        if settings.randcounter % 50 == 0:
            settings.count = (settings.count + 1) % 2
            settings.score += 1
        if settings.randcounter % 500 == 0:
            settings.dx += 0.1
        dino.shape(imglst[settings.count])
        if check_collision():
            game_over_screen()
            continue
        pen.clear()
        elapsed = time.time() - settings.start_time
        pen.write(f"Score: {settings.score} | Time: {round(elapsed, 2)}s", align="left", font=("Arial", 16, "bold"))
        jump()
        obstacle_move(obs1, obs2)
        obstacle_move(obs2, obs1)
        dust_move(dust, dust2)
        dust_move(dust2, dust)
        dust_move(dust3)
        cloud_move(cloud1)
        cloud_move(cloud2)
        time.sleep(0.01)

def init_game():
    """Инициализирует игру: загружает изображения, создает объекты"""
    global win, dino, obs1, obs2, cloud1, cloud2, dust, dust2, dust3, pen, imglst, objimg, obj1, obj2
    # Имена файлов изображений
    img = "dinoo1.1.gif"
    img1 = "dino1.1.gif"
    img2 = "dino2.1.gif"
    obj1 = "obs1.1.gif"
    awrodh = "awrodh.gif"
    binduimg = "dust.gif"
    cloudimg = "cloud.gif"
    obj2 = "obs2.1.gif"
    obj3 = "obs3.1.gif"
    obj4 = "obs4.1.gif"
    obj5 = "obs5.1.gif"
    
    imglst = [img1, img2]  # Список для анимации динозавра
    objimg = [obj1, obj2, obj3, obj4, obj5]  # Список препятствий
    elements = [img, img1, img2, awrodh, binduimg, cloudimg, obj1, obj2, obj3, obj4, obj5]
    
    # Создаем экран Turtle
    win = turtle.Screen()
    win.title("Dinosaur Game")
    win.setup(width=800, height=500)
    win.bgcolor("white")
    win.tracer(0)
    
    # Центрируем окно Turtle
    canvas = win.getcanvas()
    root = canvas.winfo_toplevel()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (800 // 2)
    y = (screen_height // 2) - (500 // 2)
    root.geometry(f"800x500+{x}+{y}")
    
    # Загружаем изображения
    for element in elements:
        try:
            win.addshape(element)
        except:
            print(f"Не удалось загрузить изображение: {element}")
    
    # Создаем объекты
    pen = turtle.Turtle()
    pen.hideturtle()
    pen.color("grey")
    pen.penup()
    pen.goto(175, 231)
    
    cloud1 = create_turtle(cloudimg, 250, 220)
    cloud2 = create_turtle(cloudimg, 250, 220)
    dust = create_turtle(awrodh, 420, 127)
    dust2 = create_turtle(awrodh, 420, 127)
    dust3 = create_turtle(awrodh, 420, 127)
    obs1 = create_turtle(obj1, 420, 140)
    obs2 = create_turtle(obj2, 700, 140)
    
    dino = turtle.Turtle()
    dino.shape(img)
    dino.penup()
    dino.goto(-255, 142)
    dino.speed(0)
    
    # Назначаем клавиши управления
    win.listen()
    win.onkeypress(lambda: setattr(settings, 'is_jumping', True), "space")
    win.onkey(reset_game, "Return")

def run_game():
    """Запускает игру с гарантированным именем игрока"""
    global username
    # Если имя еще не задано, запрашиваем его
    if username is None:
        get_username()
    
    # Инициализация и запуск игры
    init_game()
    game_loop()

def show_leaders(menu_root=None):
    """Отображает таблицу лидеров с проверкой данных"""
    if menu_root:
        menu_root.withdraw()
    
    leaders_win = Toplevel()
    leaders_win.title("Таблица лидеров")
    center_window(leaders_win, 500, 400)
    
    def on_close():
        leaders_win.destroy()
        if menu_root:
            menu_root.deiconify()
    
    leaders_win.protocol("WM_DELETE_WINDOW", on_close)
    
    # Создание текстового поля
    text = ScrolledText(leaders_win, font=("Courier New", 12), width=50, height=15)
    text.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    # Заголовок таблицы
    text.insert(END, f"{'№':<3} {'Никнейм':<15} {'Очки':<8} {'Время':<10}\n")
    text.insert(END, "-"*40 + "\n")
    
    # Загрузка и отображение данных
    try:
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                leaderboard = json.load(f)
                
                for i, entry in enumerate(leaderboard, 1):
                    # Гарантируем наличие всех полей
                    name = entry.get('name', 'Игрок')
                    score = entry.get('score', 0)
                    time_val = entry.get('time', 0.0)
                    
                    text.insert(END, f"{i:<3} {name:<15} {score:<8} {time_val:<10.2f}\n")
    except Exception as e:
        text.insert(END, f"Ошибка загрузки таблицы лидеров\n")
    
    text.config(state=DISABLED)
    
    # Кнопка закрытия
    Button(leaders_win, text="Закрыть", command=on_close, 
           font=("Arial", 12), width=15).pack(pady=10)
    
    # Кнопка закрытия
    Button(leaders_win, text="Закрыть", command=on_close, 
           font=("Arial", 12), width=15).pack(pady=10)

def show_leaders(menu_root=None):
    """Отображает таблицу лидеров с одной кнопкой закрытия"""
    if menu_root:
        menu_root.withdraw()  # Скрываем главное меню
    
    leaders_win = Toplevel()
    leaders_win.title("Таблица лидеров")
    center_window(leaders_win, 500, 400)
    leaders_win.resizable(False, False)  # Запрещаем изменение размера
    
    # Функция для закрытия окна
    def close_window():
        leaders_win.destroy()
        if menu_root:
            menu_root.deiconify()  # Восстанавливаем главное меню
    
    # Обработчик закрытия окна (крестик)
    leaders_win.protocol("WM_DELETE_WINDOW", close_window)
    
    # Основное содержимое
    main_frame = Frame(leaders_win)
    main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    # Заголовок
    Label(main_frame, text="Таблица лидеров", font=("Arial", 16, "bold")).pack(pady=(0, 10))
    
    # Таблица с прокруткой
    text_frame = Frame(main_frame)
    text_frame.pack(fill=BOTH, expand=True)
    
    text = ScrolledText(text_frame, font=("Courier New", 12), width=50, height=10)
    text.pack(fill=BOTH, expand=True)
    
    # Заполнение таблицы
    text.insert(END, f"{'№':<3} {'Никнейм':<15} {'Очки':<8} {'Время':<10}\n")
    text.insert(END, "-"*40 + "\n")
    
    try:
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                leaderboard = json.load(f)
                for i, entry in enumerate(leaderboard, 1):
                    name = entry.get('name', 'Игрок')[:15]
                    score = entry.get('score', 0)
                    time_val = entry.get('time', 0.0)
                    text.insert(END, f"{i:<3} {name:<15} {score:<8} {time_val:<10.2f}\n")
    except:
        text.insert(END, "Нет данных о рекордах\n")
    
    text.config(state=DISABLED)
    
    
    btn_frame = Frame(main_frame)
    btn_frame.pack(fill=X, pady=(10, 0))
    
    Button(btn_frame, text="Закрыть", command=close_window, 
           font=("Arial", 12), width=15).pack(pady=5)
    
    # Фокус на кнопке для удобства
    leaders_win.after(100, lambda: btn_frame.focus_set())

def show_menu():
    """Отображает главное меню игры"""
    get_username()
    root = Tk()
    root.title("Dinosaur Game")
    center_window(root, 800, 500)
    
    title_label = Label(root, text="Dinosaur Game", font=("Arial", 24, "bold"))
    title_label.pack(pady=40)
    
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 14), padding=10)
    
    frame = Frame(root)
    frame.place(relx=0.5, rely=0.5, anchor=CENTER)
    
    btn_play = ttk.Button(frame, text="Играть", command=lambda: [root.destroy(), multiprocessing.Process(target=run_game).start()])
    btn_play.pack(pady=10, fill=X)
    
    btn_rules = ttk.Button(frame, text="Правила", command=lambda: show_rules(root))
    btn_rules.pack(pady=10, fill=X)
    
    # Передаем root в функцию show_leaders для его скрытия
    btn_leaders = ttk.Button(frame, text="Таблица лидеров", command=lambda: show_leaders(root))
    btn_leaders.pack(pady=10, fill=X)
    
    btn_exit = ttk.Button(frame, text="Выход", command=root.destroy)
    btn_exit.pack(pady=10, fill=X)
    
    root.mainloop()
    
def show_rules(menu_root=None):
    """Отображает окно с правилами игры"""
    if menu_root:
        menu_root.withdraw()  # Скрываем главное меню
    
    rules_win = Toplevel()
    rules_win.title("Правила игры")
    center_window(rules_win, 600, 400)
    rules_win.resizable(False, False)
    
    def close_window():
        rules_win.destroy()
        if menu_root:
            menu_root.deiconify()  # Восстанавливаем главное меню
    
    rules_win.protocol("WM_DELETE_WINDOW", close_window)
    
    # Основное содержимое
    main_frame = Frame(rules_win)
    main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    # Заголовок
    Label(main_frame, text="Правила игры", font=("Arial", 16, "bold")).pack(pady=(0, 10))
    
    # Текст правил с прокруткой
    text_frame = Frame(main_frame)
    text_frame.pack(fill=BOTH, expand=True)
    
    text = ScrolledText(text_frame, font=("Arial", 12), width=60, height=15, wrap=WORD)
    text.pack(fill=BOTH, expand=True)
    
    rules_text = """
    Правила игры Dinosaur Game:
    1. Цель игры - продержаться как можно дольше, избегая столкновений с препятствиями.
    2. Управление:
       - Пробел: прыжок (избегание препятствий)
       - Enter: перезапуск игры после поражения
    3. Очки:
       - За каждую единицу времени начисляется 1 очко
       - Чем дольше вы играете, тем выше скорость игры
    4. Таблица лидеров:
       - Сохраняются 10 лучших результатов
       - Результаты сортируются по количеству очков и времени
    5. Особенности:
       - Игра постепенно ускоряется
       - Препятствия появляются случайным образом
       - В небе движутся облака для создания атмосферы
    Удачи в игре!"""
    
    text.insert(END, rules_text)
    text.config(state=DISABLED)
    
    # Кнопка закрытия
    btn_frame = Frame(main_frame)
    btn_frame.pack(fill=X, pady=(10, 0))
    
    Button(btn_frame, text="Закрыть", command=close_window, 
           font=("Arial", 12), width=15).pack(pady=5)
    
    # Фокус на кнопке для удобства
    rules_win.after(100, lambda: btn_frame.focus_set())
if __name__ == "__main__":
    multiprocessing.freeze_support()  # Необходимо для работы multiprocessing 
    show_menu()  # Запуск главного меню