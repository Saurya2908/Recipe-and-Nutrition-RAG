import os
import yaml
import math
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SUBS_PATH = os.path.join(BASE_DIR, "data", "substitutions.yaml")
HP_PATH = os.path.join(BASE_DIR, "configs", "health_profiles.yaml")

def load_health_profiles(path: str = HP_PATH):
    with open(path) as f:
        return yaml.safe_load(f)

def load_substitutions(path: str = SUBS_PATH):
    with open(path) as f:
        return yaml.safe_load(f)

def _ingredient_list_to_lower(ings):
    return [i.lower() for i in ings]

def violates_restrictions(recipe, restrictions):
    tags = set([t.lower() for t in recipe.get("tags", [])])
    # naive rules for demo
    if "vegan" in restrictions and "vegan" not in tags:
        return True
    if "vegetarian" in restrictions and not (("vegetarian" in tags) or ("vegan" in tags)):
        return True
    if "gluten-free" in restrictions and "gluten-free" not in tags:
        return True
    # keto is complex; here we require carbs < 20g for a simple demo
    if "keto" in restrictions and recipe.get("nutrition_per_serving", {}).get("carbs_g", 999) > 20:
        return True
    # halal detection is non-trivial; basic demo: reject obvious pork/alcohol
    if "halal" in restrictions:
        bad = {"pork", "bacon", "ham", "gelatin", "wine", "beer"}
        ings = set(_ingredient_list_to_lower(recipe.get("ingredients", [])))
        if bad & ings:
            return True
    return False

def violates_allergies(recipe, allergies):
    ings = set(_ingredient_list_to_lower(recipe.get("ingredients", [])))
    tags = set([t.lower() for t in recipe.get("tags", [])])
    if "nuts" in allergies:
        if "nuts" in [a.lower() for a in recipe.get("allergens", [])] or any(x in ings for x in ["peanut","almond","cashew","walnut","hazelnut"]):
            return True
    if "dairy" in allergies:
        if "dairy" in [a.lower() for a in recipe.get("allergens", [])] or any(x in ings for x in ["milk","cheese","butter","yogurt","cream","paneer"]):
            return True
    if "eggs" in allergies and "egg" in ings:
        return True
    if "shellfish" in allergies and any(x in ings for x in ["shrimp","prawn","crab","lobster"]):
        return True
    if "soy" in allergies and ("soy" in ings or "soy sauce" in ings or "tofu" in ings):
        return True
    if "fish" in allergies and any(x in ings for x in ["fish","salmon","tuna"]):
        return True
    return False

def violates_health(recipe, conditions, hp):
    ings = set(_ingredient_list_to_lower(recipe.get("ingredients", [])))
    tags = set([t.lower() for t in recipe.get("tags", [])])
    n = recipe.get("nutrition_per_serving", {})
    # check simple per-meal limits/requirements
    for c in conditions:
        rules = hp.get(c, {})
        avoid = set([x.lower() for x in rules.get("avoid_ingredients", [])])
        if avoid & ings:
            return True
        req_tags = set([x.lower() for x in rules.get("required_tags", [])])
        if req_tags and not (req_tags & tags):
            return True
        mx = rules.get("max_per_meal", {})
        # only check fields present in both
        for k, v in mx.items():
            if n.get(k, 0) > v:
                return True
    return False

def score_targets(recipe, targets):
    # simple L2 distance on macros if user set targets (non-zero)
    n = recipe.get("nutrition_per_serving", {})
    keys = ["calories", "protein_g", "carbs_g", "fat_g"]
    diff2 = 0.0
    weight = {"calories":1.0, "protein_g":2.0, "carbs_g":1.0, "fat_g":1.0}
    any_target = False
    for k in keys:
        t = targets.get(k, 0) if targets else 0
        if t and t > 0:
            any_target = True
            diff2 += weight[k]*((n.get(k,0)-t)**2)
    if not any_target:
        return 0.0
    return -math.sqrt(diff2)  # higher is better

def apply_health_filters(hits, restrictions, allergies, conditions, hp, targets=None, top_k=10):
    # Filter out violating recipes
    filtered = []
    for r in hits:
        if violates_restrictions(r, [x.lower() for x in restrictions]):
            continue
        if violates_allergies(r, [x.lower() for x in allergies]):
            continue
        if violates_health(r, [x.lower() for x in conditions], hp):
            continue
        filtered.append(r)

    # Rank by closeness to targets (if any), then by basic tag boosts
    def rank_key(r):
        base = score_targets(r, targets)
        tags = set([t.lower() for t in r.get("tags", [])])
        boost = 0.0
        if "low-sodium" in tags:
            boost += 0.2
        if "high-fiber" in tags:
            boost += 0.1
        if "low-sugar" in tags:
            boost += 0.1
        return (base + boost)

    filtered.sort(key=rank_key, reverse=True)
    # keep top 5-10 typically
    return filtered[:top_k]

def suggest_substitutions(ingredients):
    subs = load_substitutions()
    found = {}
    for ing in ingredients:
        key = ing.lower()
        # map common variations
        if key in subs:
            found[ing] = subs[key]
        # individual words fallback (e.g., "wheat flour" -> "wheat flour" exact handled above)
        for sk in subs:
            if sk in key and sk not in (key):
                found.setdefault(ing, subs[sk])
    return found
