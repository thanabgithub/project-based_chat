#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# Check if git is installed and accessible.
if ! command -v git >/dev/null 2>&1; then
    echo "Git is not installed or not in the PATH."
    read -rsp $'Press any key to continue...\n' -n1
    exit 1
fi

# Define lists of files and directories to skip
SKIP_FILES=("pyproject.toml" "assets/favicon.ico" "summarize_code.sh" ".gitignore" "README.md" "uv.lock" ".python-version" "alembic.ini" "db.sqlite3")
SKIP_DIRS=("alembic")

# Set the current directory's basename as the project name.
PROJECT_NAME="${PWD##*/}"

# Initialize the output file.
OUTPUT_FILE="code_summary.txt"
echo "${PROJECT_NAME}/" > "${OUTPUT_FILE}"

# Create a temporary file with sorted git files.
TMP_FILE=$(mktemp)
git ls-files | sort > "${TMP_FILE}"

# Function to check if path contains any of the skip directories
should_skip_dir() {
    local filepath=$1
    for dir in "${SKIP_DIRS[@]}"; do
        if [[ "${filepath}" == ${dir}/* || "${filepath}" == */${dir}/* ]]; then
            return 0  # true in bash
        fi
    done
    return 1  # false in bash
}

# Function to process and print a directory tree branch
print_tree_branch() {
    local filepath=$1
    local current_path=""
    local prev_parts=()
    local indent=""
    
    # Split the path into parts
    IFS='/' read -ra parts <<< "$filepath"
    
    # Compare with previous path parts
    for ((i=0; i<${#parts[@]}; i++)); do
        if [[ $i -eq $((${#parts[@]}-1)) ]]; then
            # Last component (file)
            echo "${indent}└── ${parts[i]}" >> "${OUTPUT_FILE}"
        else
            # Directory
            if [[ ${#prev_parts[@]} -le $i ]] || [[ "${prev_parts[i]}" != "${parts[i]}" ]]; then
                echo "${indent}├── ${parts[i]}/" >> "${OUTPUT_FILE}"
                indent="${indent}│   "
                prev_parts[i]="${parts[i]}"
            fi
        fi
    done
}

# Initialize variables for tree building
declare -A seen_dirs
prev_path=""

# First pass: collect all directories
while IFS= read -r filepath; do
    # Check if the current file should be skipped
    skip=false
    if should_skip_dir "$filepath"; then
        skip=true
    else
        for skip_item in "${SKIP_FILES[@]}"; do
            if [[ "${filepath,,}" == "${skip_item,,}" ]]; then
                skip=true
                break
            fi
        done
    fi

    if ! $skip; then
        dirpath=$(dirname "$filepath")
        seen_dirs["$dirpath"]=1
    fi
done < "${TMP_FILE}"

# Second pass: print the tree
while IFS= read -r filepath; do
    # Check if the current file should be skipped
    skip=false
    if should_skip_dir "$filepath"; then
        skip=true
    else
        for skip_item in "${SKIP_FILES[@]}"; do
            if [[ "${filepath,,}" == "${skip_item,,}" ]]; then
                skip=true
                break
            fi
        done
    fi

    if ! $skip; then
        # Get the directory path
        dirpath=$(dirname "$filepath")
        
        # If this is a new directory, print its structure
        if [[ "$dirpath" != "$prev_path" ]]; then
            if [[ -n "$prev_path" ]]; then
                echo "" >> "${OUTPUT_FILE}"
            fi
            # Print the directory and file
            current_indent=""
            IFS='/' read -ra dir_parts <<< "$dirpath"
            for ((i=0; i<${#dir_parts[@]}; i++)); do
                if [[ $i -eq 0 ]]; then
                    echo "├── ${dir_parts[i]}/" >> "${OUTPUT_FILE}"
                else
                    echo "${current_indent}│   ├── ${dir_parts[i]}/" >> "${OUTPUT_FILE}"
                fi
                current_indent="${current_indent}│   "
            done
            echo "${current_indent}└── $(basename "$filepath")" >> "${OUTPUT_FILE}"
            prev_path="$dirpath"
        else
            # Just print the file with the current indentation
            echo "${current_indent}└── $(basename "$filepath")" >> "${OUTPUT_FILE}"
        fi
    fi
done < "${TMP_FILE}"

# Clean up the temporary file
rm -f "${TMP_FILE}"

# Append a spacer and the "File Contents:" header
{
    echo ""
    echo "File Contents:"
    echo ""
} >> "${OUTPUT_FILE}"

# Process each git-tracked file to append its content
git ls-files | while IFS= read -r REL_PATH; do
    # Check if the file should be skipped
    skip=false
    if should_skip_dir "$REL_PATH"; then
        skip=true
    else
        for skip_item in "${SKIP_FILES[@]}"; do
            # Case-insensitive comparison
            if [[ "${REL_PATH,,}" == "${skip_item,,}" ]]; then
                skip=true
                break
            fi
        done
    fi

    if $skip; then
        echo "[SKIP] ${REL_PATH}"
    else
        if [ -f "${REL_PATH}" ]; then
            {
                echo "##### ${REL_PATH}"
                cat "${REL_PATH}"
                echo ""
                echo ""
            } >> "${OUTPUT_FILE}"
        else
            {
                echo "[WARNING] ${REL_PATH} does not exist."
                echo ""
            } >> "${OUTPUT_FILE}"
        fi
    fi
done

echo "The process is complete."
echo "Output file: ${PWD}/${OUTPUT_FILE}"
read -rsp $'Press any key to continue...\n' -n1