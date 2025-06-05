import turtle  
import time
import random
import os
import json
import multiprocessing
import sys
from tkinter import *
from tkinter import simpledialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

# Путь к файлу с результатами
LEADERBOARD_FILE = "leaderboard.json"

# Настройки игры
class GameSettings:
    def __init__(self):
        self.count = 0
        self.dx = 2
        self.pdy = 9
        self.mdy = -5
        self.randcounter = 0
        self.cloudx = 0.1
        self.score = 0
        self.distance = 25
        self.game_over = False
        self.dy = 0
        self.is_jumping = False
        self.jump_timer = 0
        self.jump_lock = False
        self.start_time = time.time()
        self.elapsed_time = 0

# Глобальные переменные
settings = GameSettings()
win = None
dino = None
obs1 = None
obs2 = None
cloud1 = None
cloud2 = None
dust = None
dust2 = None
dust3 = None
pen = None
imglst = []
objimg = []
username = ""

def center_window(window, width, height):
    """Центрирует окно на экране"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

# Сохранение в таблицу лидеров
def save_score():
    leaderboard = []
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
            try:
                leaderboard = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                leaderboard = []
    
    # Проверяем, есть ли уже запись с таким именем
    existing_entry = next((entry for entry in leaderboard if entry.get("name") == username), None)
    
    if existing_entry:
        # Обновляем запись, если новый результат лучше
        if (settings.score > existing_entry.get("score", 0) or 
            (settings.score == existing_entry.get("score", 0) and 
             settings.elapsed_time < existing_entry.get("time", float('inf')))):
            existing_entry["score"] = settings.score
            existing_entry["time"] = round(settings.elapsed_time, 2)
    else:
        # Добавляем новую запись
        leaderboard.append({
            "name": username,
            "score": settings.score,
            "time": round(settings.elapsed_time, 2)
        })
    
    # Сортируем и сохраняем топ-10
    leaderboard = sorted(leaderboard, key=lambda x: (x.get("score", 0), -x.get("time", 0)), reverse=True)[:10]
    
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(leaderboard, f, ensure_ascii=False, indent=2)

# Ввод имени пользователя при запуске
def get_username():
    global username
    while not username:
        root = Tk()
        root.withdraw()
        center_window(root, 300, 150)
        username_input = simpledialog.askstring("Никнейм", "Введите ваш никнейм (макс. 15 символов):")
        root.destroy()
        if username_input:
            username = username_input.strip()[:15]
            if not username:
                retry = messagebox.askretrycancel("Ошибка", "Никнейм не может быть пустым. Повторить ввод?")
                if not retry:
                    username = "Игрок"
                    break
        else:
            retry = messagebox.askretrycancel("Ошибка", "Никнейм не может быть пустым. Повторить ввод?")
            if not retry:
                username = "Игрок"
                break

# Создание объекта turtle
def create_turtle(shape, x, y):
    t = turtle.Turtle()
    t.shape(shape)
    t.penup()
    t.hideturtle()
    t.goto(x, y)
    return t

# Движение динозавра
def jump():
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

# Движение облаков
def cloud_move(cloud):
    cloudx = cloud.xcor()
    cloud.setx(cloudx - settings.cloudx)
    if cloudx < -300:
        cloudx = random.randint(350, 430)
        cloud.setx(cloudx)
    if -300 < cloudx < 300:
        cloud.showturtle()
    else:
        cloud.hideturtle()

# Движение пыли
def dust_move(dust_obj, other_dust=None):
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

# Движение препятствий
def obstacle_move(obstacle, other_obstacle=None):
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

# Проверка столкновений
def check_collision():
    if (dino.distance(obs1) <= settings.distance or
        dino.distance(obs2) <= settings.distance):
        return True
    return False

# Экран смерти с кнопками
def game_over_screen():
    settings.game_over = True
    settings.elapsed_time = time.time() - settings.start_time
    save_score()

    def open_leaderboard():
        show_leaders()

    def return_to_menu():
        os.execl(sys.executable, sys.executable, *sys.argv)

    over_root = Tk()
    over_root.title("Game Over")
    center_window(over_root, 300, 250)
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12), padding=10)

    Label(over_root, text="GAME OVER", font=("Arial", 20, "bold")).pack(pady=10)
    Label(over_root, text=f"Очки: {settings.score}", font=("Arial", 14)).pack()
    Label(over_root, text=f"Время: {round(settings.elapsed_time, 2)} c", font=("Arial", 12)).pack(pady=(0, 20))

    ttk.Button(over_root, text="Начать заново (Enter)", command=lambda: [over_root.destroy(), reset_game()]).pack(pady=5, fill=X)
    ttk.Button(over_root, text="Выход в меню", command=lambda: [over_root.destroy(), show_menu()]).pack(pady=5, fill=X)
    ttk.Button(over_root, text="Таблица лидеров", command=open_leaderboard).pack(pady=5, fill=X)

    over_root.mainloop()

# Сброс игры
def reset_game():
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

# Главный игровой цикл
def game_loop():
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

# Инициализация игры
def init_game():
    global win, dino, obs1, obs2, cloud1, cloud2, dust, dust2, dust3, pen, imglst, objimg, obj1, obj2
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
    imglst = [img1, img2]
    objimg = [obj1, obj2, obj3, obj4, obj5]
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
    
    # Получаем размеры экрана
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Вычисляем позицию для центрирования
    x = (screen_width // 2) - (800 // 2)
    y = (screen_height // 2) - (500 // 2)
    
    # Устанавливаем позицию окна
    root.geometry(f"800x500+{x}+{y}")
    
    for element in elements:
        try:
            win.addshape(element)
        except:
            print(f"Не удалось загрузить изображение: {element}")
    
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
    
    win.listen()
    win.onkeypress(lambda: setattr(settings, 'is_jumping', True), "space")
    win.onkey(reset_game, "Return")

# Функция запуска игры в отдельном процессе
def run_game():
    global username
    try:
        with open("username.tmp", "r") as f:
            username = f.read().strip()
    except:
        username = "Игрок"
    init_game()
    game_loop()

# Улучшенное отображение таблицы лидеров
def show_leaders():
    leaders_win = Toplevel()
    leaders_win.title("Таблица лидеров")
    center_window(leaders_win, 500, 400)
    
    # Создаем фрейм для заголовка
    header_frame = Frame(leaders_win)
    header_frame.pack(fill=X, padx=10, pady=10)
    Label(header_frame, text="Топ-10 игроков", font=("Arial", 16, "bold")).pack()
    
    # Создаем фрейм для таблицы с прокруткой
    table_frame = Frame(leaders_win)
    table_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
    
    # Создаем текстовое поле с прокруткой
    text = ScrolledText(table_frame, font=("Courier New", 12), width=50, height=15)
    text.pack(fill=BOTH, expand=True)
    
    # Заголовки таблицы
    text.insert(END, f"{'№':<3} {'Никнейм':<15} {'Очки':<8} {'Время':<10}\n")
    text.insert(END, "-"*40 + "\n")
    
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                leaderboard = json.load(f)
                for i, entry in enumerate(leaderboard, 1):
                    name = entry.get("name", "Игрок")[:15]
                    score = entry.get("score", 0)
                    time_sec = entry.get("time", 0)
                    text.insert(END, f"{i:<3} {name:<15} {score:<8} {time_sec:<10.2f}\n")
        except (json.JSONDecodeError, UnicodeDecodeError):
            text.insert(END, "Ошибка чтения данных\n")
    else:
        text.insert(END, "Нет данных о рекордах\n")
    
    text.config(state=DISABLED)
    Button(leaders_win, text="Закрыть", command=leaders_win.destroy, 
           font=("Arial", 12), width=15).pack(pady=10)

# Меню игры
def show_menu():
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
    
    btn_rules = ttk.Button(frame, text="Правила", command=show_rules)
    btn_rules.pack(pady=10, fill=X)
    
    btn_leaders = ttk.Button(frame, text="Таблица лидеров", command=show_leaders)
    btn_leaders.pack(pady=10, fill=X)
    
    btn_exit = ttk.Button(frame, text="Выход", command=root.destroy)
    btn_exit.pack(pady=10, fill=X)
    
    root.mainloop()

def show_rules():
    rules_win = Toplevel()
    rules_win.title("Правила игры")
    center_window(rules_win, 400, 300)
    Label(rules_win, text="Правила игры:", font=("Arial", 16)).pack(pady=10)
    Label(rules_win, text="1. Нажимайте ПРОБЕЛ для прыжка", wraplength=350).pack()
    Label(rules_win, text="2. ENTER — перезапуск уровня после поражения", wraplength=350).pack()
    Label(rules_win, text="3. Избегайте препятствий", wraplength=350).pack()
    Label(rules_win, text="4. Чем дольше играете, тем выше скорость", wraplength=350).pack()
    Button(rules_win, text="OK", command=rules_win.destroy).pack(pady=20)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    show_menu()

    