// script.js - Frontend interactivity for SmartMealPlanner

// ✅ 1. Submit ingredients to get AI recipes
document.addEventListener("DOMContentLoaded", function () {
    const recipeForm = document.getElementById("recipeForm");
    if (recipeForm) {
        recipeForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            const ingredients = document.getElementById("ingredients").value;

            let response = await fetch("/get_recipes", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ingredients: ingredients })
            });

            let data = await response.json();

            // Show recipes in a div
            let container = document.getElementById("recipeResults");
            container.innerHTML = "";
            data.recipes.forEach((recipe, index) => {
                container.innerHTML += `
                    <div class="recipe-card">
                        <h3>🍲 ${recipe.title}</h3>
                        <p><b>Ingredients:</b> ${recipe.ingredients}</p>
                        <p><b>Instructions:</b> ${recipe.instructions}</p>
                    </div>
                `;
            });
        });
    }

    // ✅ 2. Filter community recipes by budget
    const budgetForm = document.getElementById("budgetForm");
    if (budgetForm) {
        budgetForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            const budget = document.getElementById("budget").value;

            let response = await fetch(/filter_budget?amount=${budget});
            let data = await response.json();

            let container = document.getElementById("communityResults");
            container.innerHTML = "";
            data.recipes.forEach((recipe, index) => {
                container.innerHTML += `
                    <div class="recipe-card">
                        <h3>🥘 ${recipe.title}</h3>
                        <p><b>Ingredients:</b> ${recipe.ingredients}</p>
                        <p><b>Budget:</b> GHS ${recipe.budget}</p>
                    </div>
                `;
            });
        });
    }

    // ✅ 3. Translate recipe (Ewe / Twi)
    const translateButtons = document.querySelectorAll(".translate-btn");
    translateButtons.forEach(button => {
        button.addEventListener("click", async function () {
            const recipeId = this.dataset.id;
            const lang = this.dataset.lang;

            let response = await fetch(/translate/${recipeId}/${lang});
            let data = await response.json();

            document.getElementById(recipe-${recipeId}).innerHTML = `
                <h3>${data.title}</h3>
                <p><b>Ingredients:</b> ${data.ingredients}</p>
                <p><b>Instructions:</b> ${data.instructions}</p>
            `;
        });
    });
});