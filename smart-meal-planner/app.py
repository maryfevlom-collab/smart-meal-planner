from flask import Flask, render_template, request, redirect
import mysql.connector
import openai

app = Flask(_name_)

# OpenAI API Key
openai.api_key = "your_openai_api_key"

# Database connection
db = mysql.connector.connect (
    host="localhost", 
    user="root",
    password="yourpassword",
    database="recipe_db"
    )
cursor =db.cursor()

@app.route("/")
def index():
    return render_template("index.html")

#community recipes with budget filter
@app.route("/community", methods=["GET", "POST"])
def community():
        budget_filter = request.form.get("budget") if request.method == "POST" else None
        query = """
            SELECT c.id, c.title, c.ingredients, c.instructions, c.budget, c.user_email, 
                   IFNULL(AVG(r.rating), 0) as avg_rating
            FROM community_recipes c
            LEFT JOIN recipe_ratings r ON c.id = r.recipe_id
        """
        if budget_filter:
            query += "WHERE c.budget <= %s GROUP BY c.id ORDER BY avg_rating DESC"
            cursor.execute(query, (budget_filter,))
        else:
            query += "GROUP BY c.id ORDER BY avg_rating DESC"
            cursor.execute(query)
        recipes = cursor.fetchall()
        return render_template("community.html", recipes=recipes, budget_filter=budget_filter)

#Translation feature
@app.route("/translate/<int:recipe_id>/<lang>")
def translate_recipe(recipe_id, lang):
        cursor.execute("SELECT title, ingredients, instructions FROM community_recipes WHERE id = %s", (recipe_id,))
        recipe = cursor.fetchone()
        if not recipe:
             return "Recipe not found", 404
        
        def translate(text, lang):
             response = openai.completion.create(
                  engine="text-davinci-003",
                  prompt=f"Translate this recipe into {lang}: {text}",
                  max_tokens=200
             )
             return response.choices[0].text.strip()
        return render_template("translate.html",
                               lang=lang
                               title=translate(recipe[0], lang),
                               ingredients=translate(recipe[1], lang),
                               instructions=translate (recipe[2], lang),
    
# AI prompt with budget consideration 
    prompt = f"Suggest 2 affordable, nutritious simple recipes under {budget} Ghana Cedis using {ingredients}. Format: Title - Ingredients - Instructions -Estimated Cost - Nutrition Score"
       
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=300
        )

        raw_output = response.choices[0].text.strip().split("/n")
        
        for recipe in raw_output:
            if recipe.strip():
                recipes.append(recipe)

    return render_template("index.html", recipes=recipes)

if _name_ == "_main_":
    app.run(debug=True)