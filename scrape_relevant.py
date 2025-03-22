import os

# Directories (relative to the project root) to scan for "relevant" files.
# In this example we only include the Django server code and the React client source.
INCLUDE_DIRS = [
    os.path.join("server"),          # All of your Django project (or you can be more selective)
    os.path.join("client", "src"),   # Your React source code
]

# Directories to exclude no matter what (like virtual environments, node_modules, git metadata, etc.)
EXCLUDE_DIRS = {'venv', 'node_modules', '.git', '__pycache__', 'migrations'}

# File extensions you care about – adjust this list as needed.
ALLOWED_EXTENSIONS = {'.py', '.js', '.jsx', '.css', '.html', '.json'}

def is_included(path):
    """Check if the file's path starts with one of the INCLUDE_DIRS."""
    for inc in INCLUDE_DIRS:
        # os.path.normpath helps to standardize the path
        if os.path.normpath(path).startswith(os.path.normpath(inc)):
            return True
    return False

def should_include(filepath):
    """Decide if a file should be included based on its location and extension."""
    # Check that it's in one of our include directories.
    if not is_included(filepath):
        return False

    # Exclude if any part of the path is in the EXCLUDE_DIRS.
    parts = os.path.normpath(filepath).split(os.sep)
    if any(part in EXCLUDE_DIRS for part in parts):
        return False

    # Check extension
    _, ext = os.path.splitext(filepath)
    if ext.lower() in ALLOWED_EXTENSIONS:
        return True

    return False

output_file = 'relevant_code.txt'
with open(output_file, 'w', encoding='utf-8') as out:
    for root, dirs, files in os.walk('.'):
        # Normalize the current directory (skip directories starting with a dot or unwanted ones)
        # You could also modify dirs in-place to skip scanning into excluded directories:
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            filepath = os.path.join(root, file)
            if should_include(filepath):
                out.write(f"\n\n----- {filepath} -----\n\n")
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        out.write(f.read())
                except Exception as e:
                    out.write(f"Error reading file: {e}\n")

print(f"Scraping complete. Output written to {output_file}")
