import ibis
import pkgutil
import ibis.backends as backends

print(f"Ibis version: {ibis.__version__}")
print("Listing submodules of ibis.backends:")
for loader, module_name, is_pkg in pkgutil.iter_modules(backends.__path__):
    print(f" - {module_name} (is_pkg: {is_pkg})")

try:
    import ibis.backends.sql as sql
    print("Listing submodules of ibis.backends.sql:")
    for loader, module_name, is_pkg in pkgutil.iter_modules(sql.__path__):
        print(f"   - {module_name} (is_pkg: {is_pkg})")
except Exception as e:
    print(f"Could not list ibis.backends.sql: {e}")
