import pytest
from django.urls import get_resolver

@pytest.mark.django_db
def test_print_all_urls():
    resolver = get_resolver()

    def walk(patterns, prefix=""):
        for p in patterns:
            if hasattr(p, "url_patterns"):  # include()
                yield from walk(p.url_patterns, prefix + str(p.pattern))
            else:
                yield prefix + str(p.pattern)

    urls = sorted(set("/" + u.lstrip("/") for u in walk(resolver.url_patterns)))
    # Print in chunks to keep console readable
    print("\n--- URL PATTERNS (pytest runtime) ---")
    for u in urls:
        print(u)
    print("--- END URL PATTERNS ---\n")
