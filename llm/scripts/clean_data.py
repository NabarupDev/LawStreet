"""
Optional script to clean and validate legal data
"""
import json
import re
from pathlib import Path

def clean_text(text):
    """Clean and normalize text content"""
    if not text or text == 'nan':
        return ''
    
    text = re.sub(r'\s+', ' ', text)
    
    text = text.strip()
    
    return text

def validate_entry(entry, entry_type):
    """Validate a single data entry"""
    issues = []
    
    if 'id' not in entry or not entry['id']:
        issues.append("Missing or empty 'id' field")
    
    if 'type' not in entry or not entry['type']:
        issues.append("Missing or empty 'type' field")
    
    if 'content' not in entry or not entry['content']:
        issues.append("Missing or empty 'content' field")
    
    if 'content' in entry:
        entry['content'] = clean_text(entry['content'])
    x
    for field in ['title', 'section_title', 'offense', 'punishment']:
        if field in entry:
            entry[field] = clean_text(entry[field])
    
    return entry, issues

def clean_json_file(filepath):
    """Clean a JSON file"""
    print(f"\nCleaning {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned_data = []
    total_issues = 0
    
    for i, entry in enumerate(data):
        cleaned_entry, issues = validate_entry(entry, filepath.stem)
        
        if issues:
            print(f"  Entry {i}: {', '.join(issues)}")
            total_issues += len(issues)
        
        if cleaned_entry.get('content'):
            cleaned_data.append(cleaned_entry)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    
    removed_count = len(data) - len(cleaned_data)
    print(f"  Cleaned: {len(cleaned_data)} entries kept, {removed_count} removed")
    print(f"  Issues found: {total_issues}")
    
    return len(cleaned_data), total_issues

def generate_statistics(data_dir):
    """Generate statistics about the data"""
    stats = {
        "total_entries": 0,
        "by_type": {},
        "files": {}
    }
    
    for json_file in data_dir.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        file_stats = {
            "count": len(data),
            "types": {}
        }
        
        for entry in data:
            entry_type = entry.get('type', 'unknown')
            file_stats["types"][entry_type] = file_stats["types"].get(entry_type, 0) + 1
            stats["by_type"][entry_type] = stats["by_type"].get(entry_type, 0) + 1
            stats["total_entries"] += 1
        
        stats["files"][json_file.name] = file_stats
    
    return stats

def main():
    """Main cleaning function"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    
    if not data_dir.exists():
        print("Error: data/ directory not found. Run index_data.py first.")
        return
    
    print("Starting data cleaning process...")
    
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print("No JSON files found in data/ directory")
        return
    
    total_entries = 0
    total_issues = 0
    
    for json_file in json_files:
        if json_file.name == "README.md":
            continue
        
        entries, issues = clean_json_file(json_file)
        total_entries += entries
        total_issues += issues
    
    print("\n" + "="*50)
    print("Data Statistics:")
    print("="*50)
    
    stats = generate_statistics(data_dir)
    
    print(f"\nTotal entries: {stats['total_entries']}")
    print("\nBy type:")
    for entry_type, count in sorted(stats['by_type'].items()):
        print(f"  {entry_type}: {count}")
    
    print("\nBy file:")
    for filename, file_stats in sorted(stats['files'].items()):
        print(f"  {filename}: {file_stats['count']} entries")
    
    print("\n" + "="*50)
    print(f"Cleaning complete!")
    print(f"Total issues resolved: {total_issues}")
    print("="*50)

if __name__ == "__main__":
    main()
