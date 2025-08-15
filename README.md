Recipe & Nutrition RAG with Dietary Restrictions

What this is
- A beginner-friendly Retrieval-Augmented Generation (RAG) demo that suggests recipes based on your dietary restrictions, allergies, health conditions, and nutrition goals.
- Built with Streamlit (UI), Chroma (vector DB), and Sentence-Transformers (embeddings).
- Generation uses OpenAI if OPENAI_API_KEY is set. If not, it falls back to a simple local summarizer so you can still use it without paying.

Key features
- Dietary restriction filters (vegan, vegetarian, gluten-free, keto, halal).
- Allergy filters (nuts, dairy, eggs, shellfish, soy).
- Health conditions logic (diabetes, hypertension, celiac, lactose intolerance) loaded from configs/health_profiles.yaml.
- Ingredient substitution suggestions loaded from data/substitutions.yaml.
- Nutrition goals (calories, protein, carbs, fat) and simple day-level tracking.

Local setup
1) Install Python 3.10+ and git.
2) Optional but recommended: create and activate a virtual environment.
   - macOS/Linux: python3 -m venv .venv && source .venv/bin/activate
   - Windows (PowerShell): py -m venv .venv; .\.venv\Scripts\Activate.ps1
3) Install dependencies:
   pip install -r requirements.txt
4) (Optional) Set your OpenAI API key for better responses:
   - macOS/Linux: export OPENAI_API_KEY=sk-...
   - Windows (PowerShell): setx OPENAI_API_KEY "sk-..."
5) Ingest the sample recipe dataset into the vector DB:
   python ingest.py
6) Launch the app:
   streamlit run app.py

Using the app
- Use the sidebar to pick dietary restrictions, allergies, and health conditions.
- Set target calories & macros if desired.
- Type what you want (e.g., “I have oats and apples, need a diabates-friendly breakfast”).
- Click “Find meals” to see top suggestions with nutrition and substitutions.
- Click “Add to day” to include a recipe in your daily tracker.

Deploy to Hugging Face Spaces (recommended for an easy free link)
1) Create a new Space at https://huggingface.co/spaces and select “Streamlit” as the SDK.
2) Push this repository (files as-is) to the Space.
3) In your Space “Settings” -> “Variables”, add OPENAI_API_KEY if you want LLM generation.
4) Spaces will build automatically from requirements.txt. The public link will look like:
   https://huggingface.co/spaces/<your-username>/<your-space-name>

Deploy to Streamlit Community Cloud
1) Push this folder to a public GitHub repo.
2) Go to https://share.streamlit.io , connect your GitHub, pick the repo & the app.py entry point.
3) Add OPENAI_API_KEY in app secrets if desired.
4) You’ll get a link like https://<your-app-name>-<your-user>.streamlit.app

Lightweight evaluation
- A basic retrieval evaluation is included (eval.py). It measures whether relevant recipes are in the top-k results for a few test questions.
- Run: python eval.py

Project structure
- app.py                      # Streamlit UI
- ingest.py                   # Loads data/recipes_sample.jsonl into Chroma
- rag.py                      # RAG core: embed, retrieve, filter, generate
- utils/nutrition.py          # Health logic, scoring, substitutions
- configs/health_profiles.yaml# Health condition rules
- data/recipes_sample.jsonl   # Small starter dataset
- data/substitutions.yaml     # Ingredient substitutions
- requirements.txt
- README.md

Notes
- The sample dataset is intentionally small; replace it with your own for better results.
- If you do not use OpenAI, the app will still run and produce template-based, non-LLM responses.
