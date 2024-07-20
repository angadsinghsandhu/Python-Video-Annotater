# General Imports
import os
import argparse

def scan_directory_structure(src_dir, file_extensions, exclude_files, exclude_dirs):
    """
    Scans the directory structure of the source directory and builds a nested dictionary representation.
    
    Parameters:
    src_dir (str): The source directory to scan.
    file_extensions (list): The file extensions to look for (default is ['.py']).
    exclude_files (list): List of file names to exclude from scanning.
    exclude_dirs (list): List of directory names to exclude from scanning.
    
    Returns:
    dict: A nested dictionary representing the directory structure.
    """

    def build_nested_structure(current_dir, structure):
        for dirpath, dirnames, filenames in os.walk(current_dir):
            # Exclude specified directories
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            
            
            relative_dirpath = os.path.relpath(dirpath, src_dir)
            if relative_dirpath == '.':
                current_level = structure
            else:
                parts = relative_dirpath.split(os.sep)
                current_level = structure
                for part in parts:
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]

            for filename in filenames:
                if filename not in exclude_files and any(filename.endswith(ext) for ext in file_extensions):
                    current_level[filename] = 'file'
            
            for dirname in dirnames:
                if dirname not in current_level:
                    current_level[dirname] = {}

    def directory_structure_str(directory_structure, level=1):
        """
        Builds a string representation of the directory structure in a formatted manner.
        
        Parameters:
        directory_structure (dict): The nested dictionary representing the directory structure.
        level (int): The current depth level in the directory structure.
        """
        output = []
        tab = '\t'
        
        for key, value in directory_structure.items():
            if value == 'file':
                output.append(f"{'+' * level}f{tab * level}{key}\n")
            else:
                output.append(f"{'+' * level}d{tab * level}{key}\n")
                output.append(directory_structure_str(value, level + 1))
        
        return ''.join(output)

    directory_structure = {}
    build_nested_structure(src_dir, directory_structure)
    dir_str = directory_structure_str(directory_structure)

    return directory_structure, dir_str

def scan_file_contents(src_dir, file_extensions, exclude_files, exclude_dirs):
    """
    Scans the contents of all files with the specified extensions in the source directory and its subdirectories.
    
    Parameters:
    src_dir (str): The source directory to scan.
    file_extensions (list): The file extensions to look for (default is ['.py']).
    exclude_files (list): List of file names to exclude from scanning.
    exclude_dirs (list): List of directory names to exclude from scanning.
    
    Returns:
    dict: A dictionary with file paths as keys and their contents as values.
    """
    file_contents = {}
    
    for dirpath, dirnames, filenames in os.walk(src_dir):
        # Exclude specified directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            if any(filename.endswith(ext) for ext in file_extensions) and filename not in exclude_files:
                file_path = os.path.join(dirpath, filename)
                relative_file_path = os.path.relpath(file_path, src_dir)
                
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                file_contents[relative_file_path] = content

    return file_contents

def write_directory_structure(dir_str, file_contents, summary_file):
    """
    Writes the directory structure and file contents to the summary file.
    
    Parameters:
    dir_str (str): The formatted string representation of the directory structure.
    file_contents (dict): The dictionary containing file paths and their contents.
    summary_file (file object): The file object of the summary file to write to.
    """
    # Write the directory structure
    summary_file.write(dir_str)
    summary_file.write('\nd: directory, f: file\n\n')

    # Write the file contents
    summary_file.write('FILE CONTENTS:\n\n')
    for file_path, content in file_contents.items():
        summary_file.write(f'|||||||||||||\t\tFile: {file_path}\t\t|||||||||||||\n')
        summary_file.write(content)
        summary_file.write('\n\n')

def create_summary_file(src_dir, summary_file_path, file_extensions, exclude_files, exclude_dirs):
    """
    Creates a summary file containing the directory structure and file contents.
    
    Parameters:
    src_dir (str): The source directory to scan.
    summary_file_path (str): The path to the summary file to be created.
    file_extensions (list): The file extensions to look for.
    exclude_files (list): List of file names to exclude from scanning.
    exclude_dirs (list): List of directory names to exclude from scanning.
    """
    directory_structure, dir_str = scan_directory_structure(src_dir, file_extensions, exclude_files, exclude_dirs)
    file_contents = scan_file_contents(src_dir, file_extensions, exclude_files, exclude_dirs)

    with open(summary_file_path, 'w', encoding='utf-8') as summary_file:
        summary_file.write(f'DIRECTORY STRUCTURE: {src_dir}\n')
        write_directory_structure(dir_str, file_contents, summary_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scan a directory and create a summary file with directory structure and file contents.")
    parser.add_argument('src_dir', type=str, help="The source directory to scan.")
    parser.add_argument('summary_file_path', type=str, help="The path to the summary file to be created.")
    parser.add_argument('--file_extensions', nargs='*', default=['.py'], help="The file extensions to look for (default is ['.py']).")
    parser.add_argument('--exclude_files', nargs='*', default=[], help="List of file names to exclude from scanning.")
    parser.add_argument('--exclude_dirs', nargs='*', default=[], help="List of directory names to exclude from scanning.")

    args = parser.parse_args()

    create_summary_file(args.src_dir, args.summary_file_path, args.file_extensions, args.exclude_files, args.exclude_dirs)

# sample use:
# python summary/print.py '.' './summary/summary.txt' --file_extensions .py .txt .yaml .spec .md --exclude_dirs __pycache__ build data dist imgs legacy logs out summary
