import os
import json
import ast
import streamlit as st
import pandas as pd
from rag import RAGPipeline
from dotenv import load_dotenv
from utils.nutrition import load_health_profiles, apply_health_filters, suggest_substitutions

load_dotenv()

st.set_page_config(page_title="Recipe & Nutrition RAG", page_icon="🍽️", layout="wide")

st.title("🍽️ Recipe & Nutrition RAG")
# Check if OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    st.warning("⚠️ No OpenAI API key detected — responses will use simple templates instead of AI.")
else:
    st.success("✅ OpenAI API key detected — enhanced AI responses enabled.")

st.caption("Personalized meal suggestions with dietary restrictions, allergies, and health conditions.")

# Sidebar controls
with st.sidebar:
    st.header("Your profile")
    restrictions = st.multiselect(
        "Dietary restrictions",
        ["vegan", "vegetarian", "gluten-free", "keto", "halal"]
    )
    allergies = st.multiselect(
        "Allergies",
        ["nuts", "dairy", "eggs", "shellfish", "soy", "fish"]
    )
    conditions = st.multiselect(
        "Health conditions",
        ["diabetes", "hypertension", "celiac", "lactose_intolerance"]
    )
    st.markdown("---")
    st.header("Goals per meal (optional)")
    target_cal = st.number_input("Calories", min_value=0, value=0, step=50)
    target_pro = st.number_input("Protein (g)", min_value=0, value=0, step=5)
    target_carbs = st.number_input("Carbs (g)", min_value=0, value=0, step=5)
    target_fat = st.number_input("Fat (g)", min_value=0, value=0, step=5)
    st.markdown("---")
    if st.button("Build index (run once)"):
        rag = RAGPipeline()
        count = rag.build_index()
        st.success(f"Indexed {count} recipes.")

rag = RAGPipeline()
hp = load_health_profiles()

st.subheader("Tell us what you want to eat")
query = st.text_input("Describe your meal idea or ingredients (e.g., 'oats and apple breakfast for diabetes')")
top_k = st.slider("How many suggestions?", 1, 10, 5)

if st.button("Find meals"):
    with st.spinner("Retrieving..."):
        raw_results = rag.search(query, top_k=top_k)
        # Apply filters & scoring, passing top_k along
        results = apply_health_filters(
            raw_results,
            restrictions, allergies, conditions, hp,
            targets={"calories": target_cal, "protein_g": target_pro,
                     "carbs_g": target_carbs, "fat_g": target_fat},
            top_k=top_k
        )

    if not results:
        st.warning("No results after applying your filters. Try relaxing constraints or rebuild index.")
    else:
        st.success(f"Top {len(results)} suggestions")
        for r in results:
            with st.container(border=True):
                left, right = st.columns([2,1])
                with left:
                    st.markdown(f"**{r['title']}** — {r.get('cuisine','')}")
                    # Handle tags safely
                    tags = r.get('tags', [])
                    if isinstance(tags, str):
                        try:
                            tags = ast.literal_eval(tags) if tags.startswith("[") else [tags]
                        except:
                            tags = [tags]
                    st.caption(', '.join(tags))

                    # Handle ingredients safely
                    ings = r.get('ingredients', [])
                    if isinstance(ings, str):
                        ings = [x.strip() for x in ings.split(",") if x.strip()]
                    st.write("Ingredients:", ', '.join(ings))
                    st.write(r['instructions'])
                    subs = suggest_substitutions(r['ingredients'])
                    if subs:
                        st.write("Substitutions:")
                        for ing, opts in subs.items():
                            st.write(f"- {ing}: {', '.join(opts)}")
                with right:
                    n = r.get("nutrition_per_serving", {})
                    if isinstance(n, str):
                        try:
                            n = json.loads(n)  # convert string back to dict
                        except:
                            n = {}
                    st.metric("Calories", n.get('calories', 0))
                    st.metric("Protein (g)", n.get('protein_g', 0))
                    st.metric("Carbs (g)", n.get('carbs_g', 0))
                    st.metric("Fat (g)", n.get('fat_g', 0))
                    st.metric("Sodium (mg)", n.get('sodium_mg', 0))
                    if st.button("Add to day", key=f"add_{r['id']}"):
                        day = st.session_state.get('day', [])
                        day.append(r)
                        st.session_state['day'] = day
                        st.success("Added to your day tracker")

st.subheader("Your day tracker")
day = st.session_state.get('day', [])
if day:
    df = pd.DataFrame([{
        "title": r["title"],
        **r["nutrition_per_serving"]
    } for r in day])
    st.dataframe(df, use_container_width=True)
    totals = df.sum(numeric_only=True).to_dict()
    st.info(f"Totals — Calories: {int(totals.get('calories', 0))}, Protein: {int(totals.get('protein_g', 0))}g, Carbs: {int(totals.get('carbs_g', 0))}g, Fat: {int(totals.get('fat_g', 0))}g, Sodium: {int(totals.get('sodium_mg', 0))}mg")

st.caption("Tip: Click 'Build index' after changing the dataset in data/")
