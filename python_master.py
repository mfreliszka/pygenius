import flet as ft
import sqlite3
import os
import threading
import sys
from io import StringIO
from contextlib import redirect_stdout
import json
import time
import random

# Thread-local storage for database connections
db_local = threading.local()

# Ensure data directory exists
if not os.path.exists("data"):
    os.makedirs("data")

# Function to get a thread-local database connection
def get_db_connection():
    if not hasattr(db_local, "connection"):
        db_local.connection = sqlite3.connect("data/pythonmaster.db")
    return db_local.connection

# Function to get a cursor from the thread-local connection
def get_cursor():
    conn = get_db_connection()
    return conn.cursor()

# Initialize database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        progress TEXT,
        subscription_status TEXT DEFAULT 'free',
        streak_days INTEGER DEFAULT 0,
        last_active TEXT,
        points INTEGER DEFAULT 0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS completed_lessons (
        user_id INTEGER,
        lesson_id TEXT,
        completed_date TEXT,
        PRIMARY KEY (user_id, lesson_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS completed_quizzes (
        user_id INTEGER,
        quiz_id TEXT,
        score INTEGER,
        completed_date TEXT,
        PRIMARY KEY (user_id, quiz_id)
    )
    """)
    
    conn.commit()

# Initialize the database in the main thread
init_db()

# Sample content data
LESSONS = {
    "beginner": [
        {"id": "intro", "title": "Python Introduction", "premium": False, 
         "content": "Python is a high-level, interpreted programming language known for its readability and versatility."},
        {"id": "first_steps", "title": "First Steps to Coding", "premium": False,
         "content": "Let's write our first program:\n```python\nprint('Hello, World!')\n```"},
        {"id": "strings", "title": "Using Quotation Marks in Python Coding", "premium": False,
         "content": "Strings can be defined with single or double quotes:\n```python\nname = 'Alice'\nmessage = \"Hello, there!\"\n```"},
        {"id": "data_structures", "title": "Introduction to Basic Data Structures in Python", "premium": False,
         "content": "Python has several built-in data structures:\n- Lists: `[1, 2, 3]`\n- Dictionaries: `{'a': 1, 'b': 2}`\n- Tuples: `(1, 2, 3)`"},
        {"id": "variables", "title": "Performing Complex Assignment to Variables", "premium": True,
         "content": "Python allows complex assignments:\n```python\na, b = 10, 20\nx, y, z = [1, 2, 3]\nfirst, *rest = [1, 2, 3, 4, 5]\n```"}
    ],
    "intermediate": [
        {"id": "functions", "title": "Functions in Python", "premium": True,
         "content": "Functions allow code reuse and modularization:\n```python\ndef greet(name):\n    return f'Hello, {name}!'\n```"},
        {"id": "comprehensions", "title": "List Comprehensions", "premium": True,
         "content": "List comprehensions provide a concise way to create lists:\n```python\nsquares = [x**2 for x in range(10)]\nodd_squares = [x**2 for x in range(10) if x % 2 != 0]\n```"}
    ],
    "advanced": [
        {"id": "decorators", "title": "Python Decorators", "premium": True,
         "content": "Decorators modify the behavior of functions:\n```python\ndef log_function(func):\n    def wrapper(*args, **kwargs):\n        print(f'Calling {func.__name__}')\n        return func(*args, **kwargs)\n    return wrapper\n\n@log_function\ndef hello():\n    print('Hello')\n```"}
    ]
}

QUIZZES = {
    "beginner": [
        {
            "id": "quiz1",
            "title": "Python Basics Quiz",
            "premium": False,
            "questions": [
                {
                    "question": "What function is used to output text in Python?",
                    "options": ["console.log()", "print()", "write()", "output()"],
                    "correct": 1
                },
                {
                    "question": "Which of these is NOT a basic data type in Python?",
                    "options": ["Integer", "Array", "String", "Boolean"],
                    "correct": 1
                },
                {
                    "question": "What symbol is used for comments in Python?",
                    "options": ["//", "/*", "#", "--"],
                    "correct": 2
                }
            ]
        },
        {
            "id": "quiz2", 
            "title": "Data Structures Quiz", 
            "premium": True,
            "questions": [
                {
                    "question": "Which data structure is ordered and mutable?",
                    "options": ["List", "Tuple", "Set", "Dictionary"],
                    "correct": 0
                },
                {
                    "question": "Which method adds an element to a list?",
                    "options": ["push()", "add()", "append()", "insert()"],
                    "correct": 2
                }
            ]
        }
    ]
}

CODING_TASKS = {
    "beginner": [
        {
            "id": "task1",
            "title": "Print Even Numbers",
            "premium": False,
            "description": "Write a program that prints all even numbers between 1 and 20 using a for loop.",
            "starter_code": "# Write your code here\n\n",
            "test_code": "for i in range(1, 21):\n    if i % 2 == 0:\n        print(i)",
            "validation": "2\n4\n6\n8\n10\n12\n14\n16\n18\n20"
        },
        {
            "id": "task2",
            "title": "Sum of Numbers",
            "premium": True,
            "description": "Write a function that returns the sum of all numbers from 1 to n.",
            "starter_code": "def sum_to_n(n):\n    # Your code here\n    pass\n\n# Test with\nprint(sum_to_n(10))",
            "test_code": "def sum_to_n(n):\n    return sum(range(1, n+1))\n\nprint(sum_to_n(10))",
            "validation": "55"
        }
    ],
    "algorithms": [
        {
            "id": "algo1",
            "title": "Binary Search",
            "premium": True,
            "description": "Implement a binary search function that finds the index of a target value in a sorted array.",
            "starter_code": "def binary_search(arr, target):\n    # Your code here\n    pass\n\n# Test with\narr = [1, 3, 5, 7, 9, 11, 13, 15]\nprint(binary_search(arr, 7))\nprint(binary_search(arr, 8))",
            "test_code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n\narr = [1, 3, 5, 7, 9, 11, 13, 15]\nprint(binary_search(arr, 7))\nprint(binary_search(arr, 8))",
            "validation": "3\n-1"
        }
    ]
}

# Current user (in a real app, this would come from authentication)
CURRENT_USER = {
    "id": 1,
    "username": "student1",
    "subscription_status": "free"  # or "premium"
}

# Function to ensure user exists in the database
def ensure_user_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE id = ?", (CURRENT_USER["id"],))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (id, username, subscription_status, progress, points) VALUES (?, ?, ?, ?, ?)",
            (CURRENT_USER["id"], CURRENT_USER["username"], CURRENT_USER["subscription_status"], "{}", 0)
        )
        conn.commit()

# Helper function to run Python code safely
def run_python_code(code, timeout=5):
    result = {"output": "", "error": None, "timeout": False}
    
    # Function to execute in thread
    def execute():
        old_stdout = sys.stdout
        redirected_output = StringIO()
        sys.stdout = redirected_output
        
        try:
            exec(code)
            result["output"] = redirected_output.getvalue()
        except Exception as e:
            result["error"] = str(e)
        finally:
            sys.stdout = old_stdout
    
    # Run with timeout
    thread = threading.Thread(target=execute)
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        result["timeout"] = True
        # In a real app, you'd want to terminate the thread safely
    
    return result

# Theme configuration
def get_theme():
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#4CAF50",    # GREEN
            primary_container="#A5D6A7",  # GREEN_200
            secondary="#FFC107",  # AMBER
            background="#ECEFF1",  # BLUE_GREY_50
        )
    )

def get_navbar(page, current_route):
    selected_index = [
        "/" == current_route, 
        "/lessons" in current_route, 
        "/quizzes" in current_route, 
        "/coding" in current_route, 
        "/settings" in current_route
    ].index(True)
    
    return ft.NavigationBar(
        bgcolor="#FFFFFF",
        destinations=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.icons.HOME if selected_index == 0 else ft.icons.HOME_OUTLINED,
                            color="#4CAF50" if selected_index == 0 else "#616161",
                        ),
                        ft.Text("Home", size=12),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                margin=ft.margin.symmetric(horizontal=8),
                on_click=lambda _: page.go("/"),
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.icons.MENU_BOOK if selected_index == 1 else ft.icons.MENU_BOOK_OUTLINED,
                            color="#4CAF50" if selected_index == 1 else "#616161",
                        ),
                        ft.Text("Lessons", size=12),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                margin=ft.margin.symmetric(horizontal=8),
                on_click=lambda _: page.go("/lessons"),
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.icons.QUIZ if selected_index == 2 else ft.icons.QUIZ_OUTLINED,
                            color="#4CAF50" if selected_index == 2 else "#616161",
                        ),
                        ft.Text("Quizzes", size=12),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                margin=ft.margin.symmetric(horizontal=8),
                on_click=lambda _: page.go("/quizzes"),
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.icons.CODE if selected_index == 3 else ft.icons.CODE_OUTLINED,
                            color="#4CAF50" if selected_index == 3 else "#616161",
                        ),
                        ft.Text("Coding", size=12),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                margin=ft.margin.symmetric(horizontal=8),
                on_click=lambda _: page.go("/coding"),
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.icons.SETTINGS if selected_index == 4 else ft.icons.SETTINGS_OUTLINED,
                            color="#4CAF50" if selected_index == 4 else "#616161",
                        ),
                        ft.Text("Settings", size=12),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                margin=ft.margin.symmetric(horizontal=8),
                on_click=lambda _: page.go("/settings"),
            ),
        ],
    )

# Progress badge for lessons/quizzes
def get_progress_badge(user_id, item_id, item_type="lesson"):
    cursor = get_cursor()
    
    if item_type == "lesson":
        cursor.execute("SELECT * FROM completed_lessons WHERE user_id = ? AND lesson_id = ?", 
                      (user_id, item_id))
    else:
        cursor.execute("SELECT * FROM completed_quizzes WHERE user_id = ? AND quiz_id = ?", 
                      (user_id, item_id))
    
    if cursor.fetchone():
        return ft.Icon(ft.icons.CHECK_CIRCLE, color="#4CAF50", size=16)  # GREEN
    else:
        return ft.Container(width=16)  # Empty placeholder

# Premium content badge
def get_premium_badge(is_premium):
    if is_premium:
        return ft.Container(
            content=ft.Text("PRO", size=10, weight=ft.FontWeight.BOLD, color="white"),
            bgcolor="#FFC107",  # AMBER
            border_radius=ft.border_radius.all(4),
            padding=ft.padding.symmetric(horizontal=4, vertical=2),
        )
    else:
        return ft.Container(width=0)  # Empty space

# Home Page / Dashboard
def dashboard_view(page):
    # Get thread-local cursor
    cursor = get_cursor()
    
    # Get user stats
    cursor.execute("SELECT points, streak_days FROM users WHERE id = ?", (CURRENT_USER["id"],))
    user_stats = cursor.fetchone()
    points = user_stats[0] if user_stats else 0
    streak = user_stats[1] if user_stats else 0
    
    # Count completed items
    cursor.execute("SELECT COUNT(*) FROM completed_lessons WHERE user_id = ?", (CURRENT_USER["id"],))
    completed_lessons = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM completed_quizzes WHERE user_id = ?", (CURRENT_USER["id"],))
    completed_quizzes = cursor.fetchone()[0]
    
    # User profile section
    user_profile = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.random(), size=50, color="#4CAF50"),  # GREEN
                ft.Column([
                    ft.Text(CURRENT_USER["username"], size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        f"{'Premium' if CURRENT_USER['subscription_status'] == 'premium' else 'Free'} Plan", 
                        color="#FFC107" if CURRENT_USER["subscription_status"] == "premium" else "#616161"  # AMBER or GREY_700
                    )
                ]),
            ], alignment=ft.MainAxisAlignment.START),
            
            ft.Container(height=10),
            
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("XP Points", size=12),
                        ft.Text(str(points), size=20, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
                    border_radius=ft.border_radius.all(8),
                    bgcolor="#E8F5E9",  # GREEN_100
                    padding=10,
                    expand=True,
                ),
                ft.Container(width=10),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Streak Days", size=12),
                        ft.Text(str(streak), size=20, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
                    border_radius=ft.border_radius.all(8),
                    bgcolor="#FFF8E1",  # AMBER_100
                    padding=10,
                    expand=True,
                ),
                ft.Container(width=10),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Completed", size=12),
                        ft.Text(f"{completed_lessons + completed_quizzes}", size=20, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
                    border_radius=ft.border_radius.all(8),
                    bgcolor="#E3F2FD",  # BLUE_100
                    padding=10,
                    expand=True,
                ),
            ]),
        ]),
        padding=20,
        border_radius=ft.border_radius.all(12),
        bgcolor="white",
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.colors.BLACK12,
        )
    )
    
    # Recently accessed content
    recent_content = ft.Container(
        content=ft.Column([
            ft.Text("Continue Learning", size=16, weight=ft.FontWeight.BOLD),
            ft.Divider(height=1),
            
            ft.Container(
                content=ft.ListTile(
                    leading=ft.Icon(ft.icons.MENU_BOOK, color="#4CAF50"),  # GREEN
                    title=ft.Text("Python Introduction"),
                    subtitle=ft.Text("2% completed"),
                    trailing=ft.Icon(ft.icons.ARROW_FORWARD_IOS, size=16),
                ),
                on_click=lambda _: page.go("/lessons/intro"),
                border_radius=ft.border_radius.all(8),
                bgcolor="white",
            ),
            
            ft.Container(height=8),
            
            ft.Container(
                content=ft.ListTile(
                    leading=ft.Icon(ft.icons.QUIZ, color="#FFC107"),  # AMBER
                    title=ft.Text("Python Basics Quiz"),
                    subtitle=ft.Text("Not started"),
                    trailing=ft.Icon(ft.icons.ARROW_FORWARD_IOS, size=16),
                ),
                on_click=lambda _: page.go("/quizzes/quiz1"),
                border_radius=ft.border_radius.all(8),
                bgcolor="white",
            ),
        ]),
        padding=20,
        border_radius=ft.border_radius.all(12),
        bgcolor="#ECEFF1",  # BLUE_GREY_50
    )
    
    # Upgrade card (show only for free users)
    upgrade_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.WORKSPACE_PREMIUM, color="#FFC107", size=40),  # AMBER
                ft.Column([
                    ft.Text("Upgrade to Premium", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("Unlock all lessons, quizzes and coding exercises"),
                ], expand=True),
            ]),
            ft.Container(height=10),
            ft.ElevatedButton(
                "Upgrade Now",
                style=ft.ButtonStyle(
                    bgcolor="#FFC107",  # AMBER
                    color="white",
                ),
                width=float("inf"),
            ),
        ]),
        padding=20,
        border_radius=ft.border_radius.all(12),
        bgcolor="white",
        visible=CURRENT_USER["subscription_status"] != "premium",
    )
    
    # Assemble the view
    return ft.View(
        "/",
        [
            ft.AppBar(
                title=ft.Text("Python Master"),
                bgcolor="#4CAF50",  # GREEN
                color="white",
                center_title=False,
            ),
            ft.Container(
                content=ft.Column([
                    user_profile,
                    ft.Container(height=16),
                    recent_content,
                    ft.Container(height=16),
                    upgrade_card,
                ]),
                padding=20,
            ),
        ],
        navigation_bar=get_navbar(page, "/"),
    )

# Lessons List View
def lessons_list_view(page):
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(
                text="Beginner",
                content=ft.Column([
                    *[lesson_item(lesson, page) for lesson in LESSONS["beginner"]]
                ], scroll=ft.ScrollMode.AUTO, spacing=8, expand=True),
            ),
            ft.Tab(
                text="Intermediate",
                content=ft.Column([
                    *[lesson_item(lesson, page) for lesson in LESSONS["intermediate"]]
                ], scroll=ft.ScrollMode.AUTO, spacing=8, expand=True),
            ),
            ft.Tab(
                text="Advanced",
                content=ft.Column([
                    *[lesson_item(lesson, page) for lesson in LESSONS["advanced"]]
                ], scroll=ft.ScrollMode.AUTO, spacing=8, expand=True),
            ),
        ],
        expand=True,
    )
    
    return ft.View(
        "/lessons",
        [
            ft.AppBar(
                title=ft.Text("Lessons"),
                bgcolor="#4CAF50",  # GREEN
                color="white",
                center_title=False,
            ),
            tabs,
        ],
        navigation_bar=get_navbar(page, "/lessons"),
    )

# Single lesson item
def lesson_item(lesson, page):
    premium_badge = get_premium_badge(lesson["premium"])
    progress_badge = get_progress_badge(CURRENT_USER["id"], lesson["id"])
    
    # Check if premium content and user has free status
    is_locked = lesson["premium"] and CURRENT_USER["subscription_status"] == "free"
    
    return ft.Container(
        content=ft.ListTile(
            leading=ft.Icon(
                ft.icons.LOCK if is_locked else ft.icons.MENU_BOOK,
                color="#9E9E9E" if is_locked else "#4CAF50",  # GREY_400 or GREEN
            ),
            title=ft.Text(
                lesson["title"],
                color="#9E9E9E" if is_locked else "black",  # GREY_400 or BLACK
            ),
            subtitle=ft.Text(
                "Premium content" if is_locked else "Tap to view",
                color="#9E9E9E" if is_locked else "#616161",  # GREY_400 or GREY_700
            ),
            trailing=ft.Row([
                premium_badge,
                ft.Container(width=4),
                progress_badge,
            ], spacing=0),
        ),
        on_click=lambda _: (
            page.go(f"/lessons/{lesson['id']}") if not is_locked else 
            show_premium_dialog(page)
        ),
        bgcolor="white",
        border_radius=ft.border_radius.all(8),
    )

# Lesson Detail View
def lesson_detail_view(page, lesson_id):
    # Get thread-local cursor
    cursor = get_cursor()
    
    # Find the lesson
    lesson = None
    for category in LESSONS:
        for l in LESSONS[category]:
            if l["id"] == lesson_id:
                lesson = l
                break
        if lesson:
            break
    
    if not lesson:
        return ft.View(
            f"/lessons/{lesson_id}",
            [
                ft.AppBar(
                    title=ft.Text("Lesson Not Found"),
                    bgcolor="#4CAF50",  # GREEN
                    color="white",
                    center_title=False,
                    leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/lessons")),
                ),
                ft.Text("The requested lesson could not be found."),
            ],
        )
    
    def mark_complete():
        # Get thread-local connection and cursor
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Record completion in database
        cursor.execute(
            "INSERT OR REPLACE INTO completed_lessons (user_id, lesson_id, completed_date) VALUES (?, ?, ?)",
            (CURRENT_USER["id"], lesson_id, time.strftime("%Y-%m-%d %H:%M:%S"))
        )
        
        # Update user points
        cursor.execute(
            "UPDATE users SET points = points + ? WHERE id = ?",
            (10, CURRENT_USER["id"])
        )
        conn.commit()
        
        # Show confirmation
        page.show_snack_bar(ft.SnackBar(content=ft.Text("Lesson completed! +10 XP"), bgcolor="#4CAF50"))  # GREEN
        
        # Update UI
        page.update()
        
        # Navigate back after delay
        time.sleep(1)
        page.go("/lessons")
    
    # Check if already completed
    cursor.execute(
        "SELECT * FROM completed_lessons WHERE user_id = ? AND lesson_id = ?",
        (CURRENT_USER["id"], lesson_id)
    )
    already_completed = cursor.fetchone() is not None
    
    return ft.View(
        f"/lessons/{lesson_id}",
        [
            ft.AppBar(
                title=ft.Text(lesson["title"]),
                bgcolor="#4CAF50",  # GREEN
                color="white",
                center_title=False,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/lessons")),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Markdown(
                        lesson["content"],
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        code_theme="atom-one-dark",
                        code_style=ft.TextStyle(font_family="monospace", size=14),
                    ),
                    ft.Container(height=16),
                    ft.ElevatedButton(
                        "Mark as Complete",
                        style=ft.ButtonStyle(
                            bgcolor="#4CAF50" if not already_completed else "#9E9E9E",  # GREEN or GREY_400
                            color="white",
                        ),
                        width=float("inf"),
                        on_click=lambda _: mark_complete() if not already_completed else None,
                        disabled=already_completed,
                    ),
                    ft.Text(
                        "Already completed" if already_completed else "",
                        color="#616161",  # GREY_600
                        text_align=ft.TextAlign.CENTER,
                    ),
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                padding=20,
                expand=True,
            ),
        ],
    )

# Quizzes List View
def quizzes_list_view(page):
    categories = list(QUIZZES.keys())
    
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(
                text=category.capitalize(),
                content=ft.Column([
                    *[quiz_item(quiz, page) for quiz in QUIZZES[category]]
                ], scroll=ft.ScrollMode.AUTO, spacing=8, expand=True),
            ) for category in categories
        ],
        expand=True,
    )
    
    return ft.View(
        "/quizzes",
        [
            ft.AppBar(
                title=ft.Text("Quizzes"),
                bgcolor="#4CAF50",  # GREEN
                color="white",
                center_title=False,
            ),
            tabs,
        ],
        navigation_bar=get_navbar(page, "/quizzes"),
    )

# Single quiz item
def quiz_item(quiz, page):
    premium_badge = get_premium_badge(quiz["premium"])
    progress_badge = get_progress_badge(CURRENT_USER["id"], quiz["id"], "quiz")
    
    # Check if premium content and user has free status
    is_locked = quiz["premium"] and CURRENT_USER["subscription_status"] == "free"
    
    return ft.Container(
        content=ft.ListTile(
            leading=ft.Icon(
                ft.icons.LOCK if is_locked else ft.icons.QUIZ,
                color="#9E9E9E" if is_locked else "#FFC107",  # GREY_400 or AMBER
            ),
            title=ft.Text(
                quiz["title"],
                color="#9E9E9E" if is_locked else "black",  # GREY_400 or BLACK
            ),
            subtitle=ft.Text(
                "Premium content" if is_locked else f"{len(quiz['questions'])} questions",
                color="#9E9E9E" if is_locked else "#616161",  # GREY_400 or GREY_700
            ),
            trailing=ft.Row([
                premium_badge,
                ft.Container(width=4),
                progress_badge,
            ], spacing=0),
        ),
        on_click=lambda _: (
            page.go(f"/quizzes/{quiz['id']}") if not is_locked else 
            show_premium_dialog(page)
        ),
        bgcolor="white",
        border_radius=ft.border_radius.all(8),
    )

# Quiz Detail View
def quiz_detail_view(page, quiz_id):
    # Get thread-local cursor
    cursor = get_cursor()
    
    # Find the quiz
    quiz = None
    for category in QUIZZES:
        for q in QUIZZES[category]:
            if q["id"] == quiz_id:
                quiz = q
                break
        if quiz:
            break
    
    if not quiz:
        return ft.View(
            f"/quizzes/{quiz_id}",
            [
                ft.AppBar(
                    title=ft.Text("Quiz Not Found"),
                    bgcolor="#4CAF50",  # GREEN
                    color="white",
                    center_title=False,
                    leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/quizzes")),
                ),
                ft.Text("The requested quiz could not be found."),
            ],
        )
    
    current_question = 0
    questions = quiz["questions"]
    answers = [-1] * len(questions)
    
    # Create the quiz view elements
    question_text = ft.Text(
        questions[current_question]["question"],
        size=18,
        weight=ft.FontWeight.BOLD,
    )
    
    options_list = ft.Column(spacing=8)
    
    next_button = ft.ElevatedButton(
        "Next",
        style=ft.ButtonStyle(
            bgcolor="#4CAF50",  # GREEN
            color="white",
        ),
        width=float("inf"),
    )
    
    result_text = ft.Text("", size=20, weight=ft.FontWeight.BOLD, color="#4CAF50")  # GREEN
    
    progress_bar = ft.ProgressBar(width=float("inf"), value=0)
    
    question_container = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(f"Question 1/{len(questions)}", weight=ft.FontWeight.BOLD),
                progress_bar,
            ]),
            ft.Container(height=16),
            question_text,
            ft.Container(height=16),
            options_list,
            ft.Container(height=16),
            next_button,
            ft.Container(height=16),
            result_text,
        ]),
        padding=20,
        expand=True,
    )
    
    def update_question():
        nonlocal current_question
        
        # Update progress
        progress_bar.value = (current_question + 1) / len(questions)
        
        # Update question number and text
        question_text.value = questions[current_question]["question"]
        
        # Update options
        options_list.controls.clear()
        for i, option in enumerate(questions[current_question]["options"]):
            options_list.controls.append(
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Radio(value=str(i), selected=answers[current_question] == i),
                        title=ft.Text(option),
                    ),
                    on_click=lambda _, i=i: select_answer(i),
                    bgcolor="white",
                    border_radius=ft.border_radius.all(8),
                )
            )
        
        # Update button text
        if current_question == len(questions) - 1:
            next_button.text = "Submit"
        else:
            next_button.text = "Next"
        
        page.update()
    
    def select_answer(index):
        answers[current_question] = index
        update_question()
    
    def next_question(_):
        nonlocal current_question
        
        # If no answer selected
        if answers[current_question] == -1:
            page.show_snack_bar(ft.SnackBar(content=ft.Text("Please select an answer")))
            return
        
        if current_question < len(questions) - 1:
            # Move to next question
            current_question += 1
            update_question()
        else:
            # Calculate score
            correct_count = 0
            for i, question in enumerate(questions):
                if answers[i] == question["correct"]:
                    correct_count += 1
            
            score = int(100 * correct_count / len(questions))
            
            # Show result
            question_container.content.controls.clear()
            question_container.content.controls.extend([
                ft.Text("Quiz Complete!", size=24, weight=ft.FontWeight.BOLD, color="#4CAF50"),  # GREEN
                ft.Container(height=16),
                ft.Text(f"Your Score: {score}%", size=20),
                ft.Text(f"Correct answers: {correct_count}/{len(questions)}"),
                ft.Container(height=16),
                ft.ElevatedButton(
                    "Return to Quizzes",
                    style=ft.ButtonStyle(
                        bgcolor="#4CAF50",  # GREEN
                        color="white",
                    ),
                    width=float("inf"),
                    on_click=lambda _: page.go("/quizzes"),
                ),
            ])
            
            # Save result to database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR REPLACE INTO completed_quizzes (user_id, quiz_id, score, completed_date) VALUES (?, ?, ?, ?)",
                (CURRENT_USER["id"], quiz_id, score, time.strftime("%Y-%m-%d %H:%M:%S"))
            )
            
            # Award points
            points = correct_count * 5
            cursor.execute(
                "UPDATE users SET points = points + ? WHERE id = ?",
                (points, CURRENT_USER["id"])
            )
            conn.commit()
            
            page.update()
    
    next_button.on_click = next_question
    
    # Initial setup
    update_question()
    
    return ft.View(
        f"/quizzes/{quiz_id}",
        [
            ft.AppBar(
                title=ft.Text(quiz["title"]),
                bgcolor="#4CAF50",  # GREEN
                color="white",
                center_title=False,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/quizzes")),
            ),
            question_container,
        ],
    )

# Coding Tasks List View
def coding_tasks_list_view(page):
    categories = list(CODING_TASKS.keys())
    
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(
                text=category.capitalize(),
                content=ft.Column([
                    *[task_item(task, page, category) for task in CODING_TASKS[category]]
                ], scroll=ft.ScrollMode.AUTO, spacing=8, expand=True),
            ) for category in categories
        ],
        expand=True,
    )
    
    return ft.View(
        "/coding",
        [
            ft.AppBar(
                title=ft.Text("Coding Tasks"),
                bgcolor="#4CAF50",  # GREEN
                color="white",
                center_title=False,
            ),
            tabs,
        ],
        navigation_bar=get_navbar(page, "/coding"),
    )

# Single task item
def task_item(task, page, category):
    premium_badge = get_premium_badge(task["premium"])
    
    # Check if premium content and user has free status
    is_locked = task["premium"] and CURRENT_USER["subscription_status"] == "free"
    
    return ft.Container(
        content=ft.ListTile(
            leading=ft.Icon(
                ft.icons.LOCK if is_locked else ft.icons.CODE,
                color="#9E9E9E" if is_locked else "#2196F3",  # GREY_400 or BLUE
            ),
            title=ft.Text(
                task["title"],
                color="#9E9E9E" if is_locked else "black",  # GREY_400 or BLACK
            ),
            subtitle=ft.Text(
                "Premium content" if is_locked else "Coding challenge",
                color="#9E9E9E" if is_locked else "#616161",  # GREY_400 or GREY_700
            ),
            trailing=premium_badge,
        ),
        on_click=lambda _: (
            page.go(f"/coding/{category}/{task['id']}") if not is_locked else 
            show_premium_dialog(page)
        ),
        bgcolor="white",
        border_radius=ft.border_radius.all(8),
    )

# Coding Task Detail View
def coding_task_view(page, category, task_id):
    # Find the task
    task = None
    for t in CODING_TASKS.get(category, []):
        if t["id"] == task_id:
            task = t
            break
    
    if not task:
        return ft.View(
            f"/coding/{category}/{task_id}",
            [
                ft.AppBar(
                    title=ft.Text("Task Not Found"),
                    bgcolor="#4CAF50",  # GREEN
                    color="white",
                    center_title=False,
                    leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/coding")),
                ),
                ft.Text("The requested coding task could not be found."),
            ],
        )
    
    code_editor = ft.TextField(
        value=task["starter_code"],
        multiline=True,
        min_lines=10,
        max_lines=20,
        text_style=ft.TextStyle(
            font_family="monospace",
            size=14,
        ),
        border_color="#90A4AE",  # BLUE_GREY_300
        focused_border_color="#42A5F5",  # BLUE_400
    )
    
    output_text = ft.TextField(
        read_only=True,
        multiline=True,
        min_lines=5,
        max_lines=10,
        text_style=ft.TextStyle(
            font_family="monospace",
            size=14,
            color="black",
        ),
        border_color="#E0E0E0",  # GREY_300
    )
    
    result_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
    
    def run_code(_):
        result = run_python_code(code_editor.value)
        
        if result["error"]:
            output_text.value = f"Error: {result['error']}"
            result_text.value = "Code execution failed"
            result_text.color = "#F44336"  # RED
        elif result["timeout"]:
            output_text.value = "Execution timed out"
            result_text.value = "Your code took too long to run"
            result_text.color = "#F44336"  # RED
        else:
            output_text.value = result["output"].strip()
            
            # Check if output matches expected result
            if output_text.value.strip() == task["validation"].strip():
                result_text.value = "Correct! Your solution works"
                result_text.color = "#4CAF50"  # GREEN
                
                # Award points (only for first completion)
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE users SET points = points + ? WHERE id = ? AND NOT EXISTS (SELECT 1 FROM completed_lessons WHERE user_id = ? AND lesson_id = ?)",
                    (20, CURRENT_USER["id"], CURRENT_USER["id"], f"task_{category}_{task_id}")
                )
                
                # Record completion
                cursor.execute(
                    "INSERT OR IGNORE INTO completed_lessons (user_id, lesson_id, completed_date) VALUES (?, ?, ?)",
                    (CURRENT_USER["id"], f"task_{category}_{task_id}", time.strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
            else:
                result_text.value = "Not quite right. Try again!"
                result_text.color = "#F44336"  # RED
        
        page.update()
    
    def show_solution(_):
        code_editor.value = task["test_code"]
        page.update()
    
    return ft.View(
        f"/coding/{category}/{task_id}",
        [
            ft.AppBar(
                title=ft.Text(task["title"]),
                bgcolor="#4CAF50",  # GREEN
                color="white",
                center_title=False,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/coding")),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text(task["description"], size=16),
                    ft.Container(height=16),
                    ft.Text("Your Code:", weight=ft.FontWeight.BOLD),
                    code_editor,
                    ft.Container(height=8),
                    ft.Row([
                        ft.ElevatedButton(
                            "Run Code",
                            style=ft.ButtonStyle(
                                bgcolor="#2196F3",  # BLUE
                                color="white",
                            ),
                            on_click=run_code,
                            expand=True,
                        ),
                        ft.Container(width=8),
                        ft.OutlinedButton(
                            "Show Solution",
                            on_click=show_solution,
                            expand=True,
                        ),
                    ]),
                    ft.Container(height=16),
                    ft.Text("Output:", weight=ft.FontWeight.BOLD),
                    output_text,
                    ft.Container(height=8),
                    result_text,
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                padding=20,
                expand=True,
            ),
        ],
    )

# Settings View
def settings_view(page):
    # Toggle subscription for demo purposes
    def toggle_subscription(_):
        CURRENT_USER["subscription_status"] = "premium" if CURRENT_USER["subscription_status"] == "free" else "free"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET subscription_status = ? WHERE id = ?",
            (CURRENT_USER["subscription_status"], CURRENT_USER["id"])
        )
        conn.commit()
        page.go("/settings")  # Refresh page
    
    return ft.View(
        "/settings",
        [
            ft.AppBar(
                title=ft.Text("Settings"),
                bgcolor="#4CAF50",  # GREEN
                color="white",
                center_title=False,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.LANGUAGE, color="#4CAF50"),  # GREEN
                            ft.Text("Change Language", size=16),
                        ]),
                        bgcolor="white",
                        padding=15,
                        border_radius=ft.border_radius.all(8),
                    ),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.STAR_OUTLINE, color="#4CAF50"),  # GREEN
                            ft.Text("Achievements", size=16),
                        ]),
                        bgcolor="white",
                        padding=15,
                        border_radius=ft.border_radius.all(8),
                    ),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.SHARE, color="#4CAF50"),  # GREEN
                            ft.Text("Share", size=16),
                        ]),
                        bgcolor="white",
                        padding=15,
                        border_radius=ft.border_radius.all(8),
                    ),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.LOCK, color="#4CAF50"),  # GREEN
                            ft.Text("Licenses", size=16),
                        ]),
                        bgcolor="white",
                        padding=15,
                        border_radius=ft.border_radius.all(8),
                    ),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.PRIVACY_TIP, color="#4CAF50"),  # GREEN
                            ft.Text("Privacy Policy", size=16),
                        ]),
                        bgcolor="white",
                        padding=15,
                        border_radius=ft.border_radius.all(8),
                    ),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(
                                ft.icons.WORKSPACE_PREMIUM, 
                                color="#FFC107" if CURRENT_USER["subscription_status"] == "premium" else "#9E9E9E"  # AMBER or GREY_400
                            ),
                            ft.Text(
                                f"Subscription Status: {CURRENT_USER['subscription_status'].capitalize()}",
                                size=16,
                            ),
                        ]),
                        bgcolor="white",
                        padding=15,
                        border_radius=ft.border_radius.all(8),
                    ),
                    ft.Container(height=16),
                    ft.Container(
                        content=ft.ElevatedButton(
                            "Toggle Subscription (Demo)",
                            style=ft.ButtonStyle(
                                bgcolor="#FFC107",  # AMBER
                                color="white",
                            ),
                            width=float("inf"),
                            on_click=toggle_subscription,
                        ),
                        padding=ft.padding.symmetric(horizontal=20),
                    ),
                    ft.Container(height=16),
                    ft.Container(
                        content=ft.Text(
                            "Check out our other apps:",
                            color="#616161",  # GREY_700
                        ),
                        padding=ft.padding.only(left=20),
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Container(
                                        content=ft.Image(
                                            src="https://placehold.co/60x60/0066ff/FFFFFF/png?text=C++",
                                            width=60,
                                            height=60,
                                        ),
                                        border_radius=ft.border_radius.all(12),
                                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                                    ),
                                    ft.Container(height=4),
                                    ft.Text("Learn C++", size=12),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=10,
                            ),
                            ft.Container(
                                content=ft.Column([
                                    ft.Container(
                                        content=ft.Image(
                                            src="https://placehold.co/60x60/f44336/FFFFFF/png?text=Java",
                                            width=60,
                                            height=60,
                                        ),
                                        border_radius=ft.border_radius.all(12),
                                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                                    ),
                                    ft.Container(height=4),
                                    ft.Text("Java Master", size=12),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=10,
                            ),
                        ], alignment=ft.MainAxisAlignment.START),
                        padding=ft.padding.symmetric(horizontal=10),
                    ),
                ], scroll=ft.ScrollMode.AUTO),
                padding=20,
            ),
        ],
        navigation_bar=get_navbar(page, "/settings"),
    )

# Premium content dialog
def show_premium_dialog(page):
    def close_dialog(_):
        dialog.open = False
        page.update()
    
    dialog = ft.AlertDialog(
        title=ft.Text("Premium Content"),
        content=ft.Text("This content is only available to premium subscribers. Upgrade to access all lessons, quizzes, and coding exercises."),
        actions=[
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.ElevatedButton(
                "Upgrade",
                style=ft.ButtonStyle(
                    bgcolor="#FFC107",  # AMBER
                    color="white",
                ),
                on_click=close_dialog,
            ),
        ],
    )
    
    page.dialog = dialog
    dialog.open = True
    page.update()

# Main app function
def main(page: ft.Page):
    # Configure page
    page.title = "Python Master"
    page.theme = get_theme()
    page.bgcolor = "#ECEFF1"  # BLUE_GREY_50
    
    # Ensure the user exists
    ensure_user_exists()
    
    # Set up routes
    def route_change(e):
        route = page.route
        
        # Make sure the user exists in this thread too
        ensure_user_exists()
        
        if route == "/":
            page.views.clear()
            page.views.append(dashboard_view(page))
        elif route == "/lessons":
            page.views.clear()
            page.views.append(lessons_list_view(page))
        elif route.startswith("/lessons/"):
            lesson_id = route.split("/")[-1]
            page.views.clear()
            page.views.append(lesson_detail_view(page, lesson_id))
        elif route == "/quizzes":
            page.views.clear()
            page.views.append(quizzes_list_view(page))
        elif route.startswith("/quizzes/"):
            quiz_id = route.split("/")[-1]
            page.views.clear()
            page.views.append(quiz_detail_view(page, quiz_id))
        elif route == "/coding":
            page.views.clear()
            page.views.append(coding_tasks_list_view(page))
        elif route.startswith("/coding/"):
            parts = route.split("/")
            if len(parts) >= 4:
                category, task_id = parts[2], parts[3]
                page.views.clear()
                page.views.append(coding_task_view(page, category, task_id))
        elif route == "/settings":
            page.views.clear()
            page.views.append(settings_view(page))
        
        page.update()
    
    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route)
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Initial route
    page.go("/")

ft.app(main, view=ft.WEB_BROWSER)