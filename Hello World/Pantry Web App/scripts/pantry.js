const input = document.getElementById('ingredientInput');
const addBtn = document.getElementById('addBtn');
const list = document.getElementById('pantryList');
const clearBtn = document.getElementById('clearBtn');

const dbName = 'SmartPantryDB';
const storeName = 'ingredients';

// Smart Pantry IndexedDB Database
function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(dbName, 1);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      if (!db.objectStoreNames.contains(storeName)) {
        db.createObjectStore(storeName, {
          keyPath: 'id',
          autoIncrement: true
        });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject('Database could not be opened.');
  });
}

// Smart Pantry Ingredient list
async function saveIngredient(name) {
  const db = await openDatabase();
  const transaction = db.transaction(storeName, 'readwrite');
  const store = transaction.objectStore(storeName);

  store.add({
    name: name,
    dateAdded: new Date().toISOString()
  });
}

async function getIngredients() {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.getAll();

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject('Ingredients could not be loaded.');
  });
}

async function deleteIngredient(id) {
  const db = await openDatabase();
  const transaction = db.transaction(storeName, 'readwrite');
  const store = transaction.objectStore(storeName);

  store.delete(id);
}

async function clearIngredients() {
  const db = await openDatabase();
  const transaction = db.transaction(storeName, 'readwrite');
  const store = transaction.objectStore(storeName);

  store.clear();
}

function addToList(ingredient) {
  const li = document.createElement('li');

  li.textContent = ingredient.name;
  li.dataset.id = ingredient.id;
  li.dataset.ingredient = ingredient.name;

  const btn = document.createElement('button');
  btn.textContent = '×';

  btn.onclick = async () => {
    await deleteIngredient(ingredient.id);
    li.remove();
    showAlmostRecipes();
  };

  li.appendChild(btn);
  list.appendChild(li);
}

// Smart Pantry 
async function loadPantry() {
  const items = await getIngredients();

  list.innerHTML = '';

  items.forEach(item => {
    addToList(item);
  });

  showAlmostRecipes();
}

addBtn.onclick = async () => {
  const value = input.value.trim().toLowerCase();

  if (value) {
    await saveIngredient(value);
    input.value = '';
    input.focus();
    loadPantry();
  }
};

input.addEventListener('keypress', e => {
  if (e.key === 'Enter') {
    addBtn.click();
  }
});

clearBtn.onclick = async () => {
  if (confirm('Clear your entire pantry?')) {
    await clearIngredients();
    list.innerHTML = '';
    showAlmostRecipes();
  }
};

// Smart Pantry Almost Recipes
async function showAlmostRecipes() {
  try {
    const response = await fetch('data/recipes.json');
    const allRecipes = await response.json();

    const pantryItems = await getIngredients();
    const pantry = pantryItems.map(item => item.name.toLowerCase());
    const container = document.getElementById('almostRecipes');

    const almost = allRecipes
      .map(recipe => {
        const missing = recipe.ingredients.filter(item => !pantry.includes(item.toLowerCase()));

        return {
          ...recipe,
          missing: missing
        };
      })
      .filter(recipe => recipe.missing.length > 0 && recipe.missing.length <= 2)
      .sort((a, b) => a.missing.length - b.missing.length)
      .slice(0, 6);

    if (almost.length === 0) {
      container.innerHTML = '<p style="text-align:center; padding:3rem; font-size:1.2rem; opacity:0.8;">No recipes close yet. Keep adding ingredients!</p>';
      return;
    }

    container.innerHTML = almost.map(recipe => {
      return `
        <div class="almost-recipe">
          <h4>${recipe.name}</h4>
          <div class="missing-ingredients">
            ${recipe.missing.map(item => `<span>${item}</span>`).join(' ')}
          </div>
          <p class="meta">Time: ${recipe.time} • Serves ${recipe.serves}</p>
        </div>
      `;
    }).join('');
  } catch (error) {
    console.log('Could not load almost ready recipes.', error);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadPantry();
});
