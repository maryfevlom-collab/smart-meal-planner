from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv() # Loads variables from .env file

app = Flask(__name__)
app.secret_key = 'well-here-is-our-secret-key-for-app'  # Needed for sessions! Make this strong.

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # The route to redirect to if a user needs to login

# Custom handler for unauthorized users - THIS IS THE KEY FIX
@login_manager.unauthorized_handler
def unauthorized():
    # Flash a message to the user
    flash("You must be logged in to access this feature.", "error")
    # Redirect them to the login page
    return redirect(url_for('login'))

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="recipe_db"
)

def get_cursor():
    global db
    try:
        db.ping(reconnect=True, attempts=3, delay=5) # Check if connection is alive
    except mysql.connector.Error:
        # Reconnect if needed
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="recipe_db"
        )
    return db.cursor()

    # This class represents a user for Flask-Login user model and loader
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# This callback is used to reload the user object from the user ID stored in the session.
@login_manager.user_loader
def load_user(user_id):
    with get_cursor() as cursor:
        cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
    if user_data:
        return User(id=user_data[0], username=user_data[1])
    return None

#Routes
# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_cursor() as cursor:
            # Get user from DB
            cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            
            # Check if user exists and password is correct
            if user_data and check_password_hash(user_data[2], password):
                user_obj = User(id=user_data[0], username=user_data[1])
                login_user(user_obj)
                return redirect(url_for('homepage'))
            else:
                # return "Invalid username or password", 401
                flash("Invalid username or password.", "error")
                return render_template('login.html')
                
    return render_template('login.html')

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                    (username, hashed_password, email)
                )
                db.commit()
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            return "Username or email already exists", 409
    return render_template('register.html')

# Logout Route
@app.route('/logout')
@login_required  # Only logged-in users can logout
def logout():
    logout_user()
    return redirect(url_for('index'))

#Dashboard route
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/homepage")
def homepage():
    return render_template("homepage.html")

# Community recipes with budget filter
@app.route("/community")
@login_required
def community():
    # Get filter from URL parameters (from the GET form)
    budget_filter = request.args.get("budget")

    # Use the cursor inside a 'with' block. It will auto-close at the end.
    with get_cursor() as cursor:
        query = """
            SELECT c.id, c.title, c.ingredients, c.instructions, c.budget, c.created_by, 
                IFNULL(AVG(r.rating), 0) as avg_rating
            FROM community_recipes c
            LEFT JOIN recipe_ratings r ON c.id = r.recipe_id
        """
        
        if budget_filter:
            query += " WHERE c.budget <= %s GROUP BY c.id ORDER BY avg_rating DESC"
            cursor.execute(query, (budget_filter,))
        else:
            query += " GROUP BY c.id ORDER BY avg_rating DESC LIMIT 5"
            cursor.execute(query)
            
        recipes = cursor.fetchall()
    return render_template("community.html", recipes=recipes, budget_filter=budget_filter)   

#About route
@app.route("/about")
def about_us():
    return render_template("about.html")

# Translation feature
@app.route("/translate/<int:recipe_id>/<lang>")
def translate_recipe(recipe_id, lang):
    with get_cursor() as cursor:
        cursor.execute("SELECT title, ingredients, instructions FROM community_recipes WHERE id = %s", (recipe_id,))
        recipe = cursor.fetchone()
        if not recipe:
            return "Recipe not found", 404
        
        def translate(text, lang):
            # Gemini API call for translation
            try:
                prompt = f"Translate the following recipe text into {lang}. Only return the translation, nothing else: {text}"
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                # If the API call fails, fall back to simulation
                print(f"Gemini API Error during translation: {e}")
                return f"Sorry, translation failed please try again later."
                # flash("Sorry, connect to internet to see transalation", "error")
    	
    return render_template("translated_recipe.html",
                           lang=lang,
                           title=translate(recipe[0], lang),
                           ingredients=translate(recipe[1], lang),
                           instructions=translate(recipe[2], lang))

# AI prompt with budget consideration 
@app.route("/generate-recipes", methods=["POST"])
def generate_recipes():
    budget = request.form.get("budget")
    ingredients = request.form.get("ingredients")
    
    # Try the real Gemini API call
    try:
        prompt = f"""Generate exactly 2 recipes using these ingredients: {ingredients} with a total budget of {budget} Ghana Cedis.

    IMPORTANT: For each recipe, provide output in this exact format using ' - ' as separators:
    Title - Comma-separated ingredients - Step-by-step instructions - Estimated Cost in GHS - Nutrition score/10 (Nutrition details)

    Example:
    Jollof Rice - Rice, tomato, onion, chicken - Cook rice. Fry ingredients. Mix together - GHS 20 - 8/10 (Good source of carbs, protein)

    Requirements:
    1. Use only ' - ' as separators, no other formatting
    2. No bullet points, numbers, or markdown
    3. Keep instructions concise with steps separated by periods
    4. Include exact cost estimate in GHS format
    5. Provide nutrition score out of 10 with brief details in parentheses

    Now generate 2 recipes:"""
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        print("Gemini Raw Output:\n", raw_text)  # Good for debugging
    except Exception as e:
        print(f"Gemini API Error: {e}. Using simulation.")
        raw_text = """Jollof Rice - Rice, tomato, onion, chicken - Cook rice. Fry ingredients. Mix together - GHS 20 - 8/10 (Good source of carbs, protein)
    Tomato Stew - Tomato, onion, chicken - Boil chicken. Fry tomatoes. Combine - GHS 17 - 7/10 (Good source of vitamins)"""

    # Process the recipes
    formatted_recipes = []
    for line in raw_text.split('\n'):
        line = line.strip()
        if line and ' - ' in line:
            # Remove any markdown formatting that might still be present
            line = line.replace('**', '').replace('*', '')
            
            parts = line.split(' - ', 4)  # Split into max 5 parts
            if len(parts) == 5:
                formatted_recipes.append({
                    'title': parts[0].strip(),
                    'ingredients': parts[1].strip(),
                    'instructions': parts[2].strip(),
                    'cost': parts[3].strip(),
                    'nutrition': parts[4].strip()
                })
            elif len(parts) >= 4:
                # Handle cases where nutrition info might be missing
                formatted_recipes.append({
                    'title': parts[0].strip(),
                    'ingredients': parts[1].strip(),
                    'instructions': parts[2].strip(),
                    'cost': parts[3].strip(),
                    'nutrition': parts[4].strip() if len(parts) > 4 else 'Not specified'
                })
            else:
                # Fallback if parsing fails
                formatted_recipes.append({'title': 'Recipe', 'full_text': line})
        elif line.strip():
            # Skip lines that don't contain recipe data
            if not any(keyword in line.lower() for keyword in ['recipe', 'ingredients', 'instructions']):
                formatted_recipes.append({'title': 'Recipe', 'full_text': line})

    return render_template("generated_recipes.html", 
                         recipes=formatted_recipes,
                         original_ingredients=ingredients,
                         original_budget=budget)

# Add a new recipe to the community
@app.route("/add_recipe", methods=["POST"])
@login_required
def add_recipe():
    # Get form data
    title = request.form.get("title")
    ingredients = request.form.get("ingredients")
    instructions = request.form.get("instructions")
    budget = request.form.get("budget")
    created_by = current_user.id

    with get_cursor() as cursor:
        # Insert into database
        query = """
            INSERT INTO community_recipes (title, ingredients, instructions, budget, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        try:
            cursor.execute(query, (title, ingredients, instructions, budget, created_by))
            db.commit()  # Important! Save the changes to the database.

            flash("Thank you recipe added to community", "success")
        except Exception as e:
            flash("Please fill the form first", "error")

    return redirect(url_for("community"))  # Redirect back to the community page

#All recipes
@app.route("/all-recipes")
def all_recipes():
    # Retrieve all recipes from the database
    with get_cursor() as cursor:
        query = """
        SELECT c.id, c.title, c.ingredients, c.instructions, c.budget, c.created_by, 
       u.username,  
       IFNULL(AVG(r.rating), 0) as avg_rating
       FROM community_recipes c
       LEFT JOIN recipe_ratings r ON c.id = r.recipe_id
        JOIN users u ON c.created_by = u.id  
        """

        query += " GROUP BY c.id ORDER BY avg_rating DESC"
        cursor.execute(query)
            
        recipes = cursor.fetchall()    
    return render_template("all_recipes.html", recipes=recipes)

#My recipes
@app.route("/my-recipes")
def my_recipes():
    # Get the current user's ID from the session
    user_id = current_user.id
    
    if not user_id:
        # Handle case where user is not logged in
        flash('Please log in to view your recipes', 'error')
        return redirect(url_for('login'))
    
    # Retrieve only the current user's recipes from the database
    with get_cursor() as cursor:
        query = """
        SELECT c.id, c.title, c.ingredients, c.instructions, c.budget, c.created_by, 
               u.username,  
               IFNULL(AVG(r.rating), 0) as avg_rating
        FROM community_recipes c
        LEFT JOIN recipe_ratings r ON c.id = r.recipe_id
        JOIN users u ON c.created_by = u.id 
        WHERE c.created_by = %s
        GROUP BY c.id 
        ORDER BY avg_rating DESC
        """
        
        cursor.execute(query, (user_id,))
        recipes = cursor.fetchall()    
    return render_template("my_recipes.html", recipes=recipes)

#leaderboard
@app.route("/leaderboard")
@login_required
def leaderboard():
    with get_cursor() as cursor:
        # Query for Top Contributors
        top_users_query = """
            SELECT u.username, COUNT(cr.id) as recipe_count
            FROM users u
            JOIN community_recipes cr ON u.id = cr.created_by
            GROUP BY u.id
            ORDER BY recipe_count DESC
            LIMIT 5
        """
        cursor.execute(top_users_query)
        top_users = cursor.fetchall()

    with get_cursor() as cursor:
        # Query for Most Affordable Recipes
        affordable_query = """
            SELECT title, budget
            FROM community_recipes
            ORDER BY budget ASC
            LIMIT 5
        """
        cursor.execute(affordable_query)
        affordable_recipes = cursor.fetchall()

    with get_cursor() as cursor: #one cursor for one query/ database interaction
        # Query for Popular Recipes (using likes)
        popular_query = """
            SELECT title, likes
            FROM community_recipes
            ORDER BY likes DESC
            LIMIT 5
        """
        cursor.execute(popular_query)
        popular_recipes = cursor.fetchall()

    return render_template("leaderboard.html",
                         top_users=top_users,
                         affordable_recipes=affordable_recipes,
                         popular_recipes=popular_recipes)

if __name__ == "__main__":
    app.run(debug=True)
