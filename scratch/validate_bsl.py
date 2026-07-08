import sys
import os

# Add project root to sys.path
# Since this script is in scratch/, the root is one level up
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.engine.bsl_dictionary import BSL_MAPPING
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    print(f"Current Path: {sys.path}")
    sys.exit(1)

tables = set(BSL_MAPPING.get('tables', {}).keys())
metrics = BSL_MAPPING.get('metrics', {})
dimensions = BSL_MAPPING.get('dimensions', {})
synonyms = BSL_MAPPING.get('synonyms', {})

errors = []

# Check table references in metrics
for m_key, info in metrics.items():
    t_ref = info.get('table')
    if t_ref not in tables:
        errors.append(f"Metric '{m_key}' references non-existent table '{t_ref}'")

# Check table references in dimensions
for d_key, info in dimensions.items():
    t_ref = info.get('table')
    if t_ref not in tables:
        errors.append(f"Dimension '{d_key}' references non-existent table '{t_ref}'")

# Check synonym targets
for s_key, target in synonyms.items():
    if target not in metrics and target not in dimensions:
        errors.append(f"Synonym '{s_key}' points to non-existent concept '{target}'")

# Check for malformed keys (anything starting with ... or containing weird chars)
all_keys = list(tables) + list(metrics.keys()) + list(dimensions.keys())
for key in all_keys:
    if not key or key.startswith('.') or ' ' in key or '..' in key or '...' in key:
        errors.append(f"Malformed key found: '{key}'")

if errors:
    print(f"FAILED: Found {len(errors)} structural errors:")
    print("\n".join(f"  - {err}" for err in errors))
else:
    print("SUCCESS: No structural errors found in BSL dictionary.")
