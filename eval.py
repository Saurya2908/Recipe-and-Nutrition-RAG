import json
from rag import RAGPipeline

# Very small toy eval: checks if a relevant recipe is in top-k for simple queries.
eval_set = [
    {"query": "high protein gluten-free lunch", "must_have_any_of": ["Grilled Chicken Quinoa Salad","Baked Salmon with Veggies"]},
    {"query": "vegan high fiber dinner", "must_have_any_of": ["Chickpea & Spinach Curry","Lentil Soup with Herbs","Tofu Stir-Fry with Brown Rice"]},
    {"query": "diabetes friendly breakfast with oats", "must_have_any_of": ["Oats & Apple Cinnamon Bowl"]},
]

if __name__ == "__main__":
    rag = RAGPipeline()
    results = []
    for case in eval_set:
        hits = rag.search(case["query"], top_k=5)
        titles = [h["title"] for h in hits]
        ok = any(x in titles for x in case["must_have_any_of"])
        results.append({"query": case["query"], "retrieved_titles": titles, "pass": ok})
    print(json.dumps(results, indent=2))
