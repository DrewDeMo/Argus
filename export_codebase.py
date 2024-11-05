import os

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"

def main():
    # List of important files to export
    files = [
        'app.py',
        'index.html',
        'style.css',
        'config.py',
        'audit_logic.py',
        'api/index.py',
        'requirements.txt',
        'vercel.json'
    ]

    # Create output string
    output = []
    
    # Add a header
    output.append("# Argus Codebase Export\n")
    
    # Read each file
    for file_path in files:
        output.append(f"\n## File: {file_path}\n")
        output.append("```")
        
        # Add file extension for proper code highlighting
        extension = os.path.splitext(file_path)[1]
        if extension:
            output.append(extension[1:])  # Remove the dot
        
        output.append("\n")
        content = read_file(file_path)
        output.append(content)
        output.append("\n```\n")

    # Write to output file
    with open('codebase_export.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

if __name__ == "__main__":
    main()
    print("Codebase exported to codebase_export.md")
