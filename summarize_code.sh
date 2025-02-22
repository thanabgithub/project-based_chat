#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# Check if git is installed and accessible.
if ! command -v git >/dev/null 2>&1; then
    echo "Git is not installed or not in the PATH."
    read -rsp $'Press any key to continue...\n' -n1
    exit 1
fi

# Define a list of files to skip.
SKIP_LIST=("pyproject.toml" "assets/favicon.ico" "summarize_code.sh" ".gitignore" "README.md" "uv.lock" ".python-version")

# Set the current directory's basename as the project name.
PROJECT_NAME="${PWD##*/}"

# Initialize the output file.
OUTPUT_FILE="code_summary.txt"
echo "${PROJECT_NAME}/" > "${OUTPUT_FILE}"

# Create a temporary file with sorted git files.
TMP_FILE=$(mktemp)
git ls-files | sort > "${TMP_FILE}"

# Process each file to build a directory tree.
while IFS= read -r filepath; do
    # Check if the current file should be skipped.
    skip=false
    for skip_item in "${SKIP_LIST[@]}"; do
        if [[ "${filepath,,}" == "${skip_item,,}" ]]; then
            skip=true
            break
        fi
    done

    if ! $skip; then
        # Split the path by '/' into an array.
        IFS='/' read -ra parts <<< "$filepath"
        indent=""
        for (( i=0; i<${#parts[@]}; i++ )); do
            part="${parts[i]}"
            if (( i < ${#parts[@]} - 1 )); then
                echo "${indent}├── ${part}/" >> "${OUTPUT_FILE}"
                indent="${indent}│   "
            else
                echo "${indent}└── ${part}" >> "${OUTPUT_FILE}"
            fi
        done
    fi
done < "${TMP_FILE}"

# Clean up the temporary file.
rm -f "${TMP_FILE}"

# Append a spacer and the "File Contents:" header.
{
    echo ""
    echo "File Contents:"
    echo ""
} >> "${OUTPUT_FILE}"

# Process each git-tracked file to append its content.
git ls-files | while IFS= read -r REL_PATH; do
    # Convert the file path to a normalized version (if needed).
    skip=false
    for skip_item in "${SKIP_LIST[@]}"; do
        # Case-insensitive comparison.
        if [[ "${REL_PATH,,}" == "${skip_item,,}" ]]; then
            skip=true
            break
        fi
    done

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
