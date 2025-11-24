try:
    from rapidfuzz import fuzz
    print(f"Apple vs Banana: {fuzz.token_set_ratio('Apple', 'Banana')}")
    print(f"Apple vs App: {fuzz.token_set_ratio('Apple', 'App')}")
except ImportError:
    print("rapidfuzz not installed")
    from difflib import SequenceMatcher
    print(f"Apple vs Banana (difflib): {SequenceMatcher(None, 'Apple', 'Banana').ratio() * 100}")
