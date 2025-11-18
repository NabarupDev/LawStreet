"""
Restore and process raw data files into the format expected by index_data.py
"""
import json
from pathlib import Path

def restore_data():
    base_dir = Path(__file__).parent.parent
    raw_dir = base_dir / "Data" / "raw"
    data_dir = base_dir / "Data"
    
    print("Restoring and processing data from raw sources...\n")
    
    print("Processing IPC...")
    raw_ipc_path = raw_dir / "Indian-Law-Penal-Code-Json" / "ipc.json"
    if raw_ipc_path.exists():
        raw_ipc = json.load(open(raw_ipc_path, encoding='utf-8'))
        processed_ipc = []
        for i, item in enumerate(raw_ipc):
            section_num = str(item.get('Section', item.get('section', i)))
            processed_ipc.append({
                "id": f"ipc_section_{section_num}",
                "type": "ipc",
                "chapter": item.get('chapter'),
                "chapter_title": item.get('chapter_title', ''),
                "section": section_num,
                "section_title": item.get('section_title', ''),
                "content": item.get('section_desc', ''),
                "metadata": {
                    "source": "Indian Penal Code",
                    "chapter": item.get('chapter'),
                    "section": section_num
                }
            })
        json.dump(processed_ipc, open(data_dir / "ipc.json", 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        print(f"  ✓ Processed {len(processed_ipc)} IPC sections")
    
    print("Processing CrPC...")
    raw_crpc_path = raw_dir / "Indian-Law-Penal-Code-Json" / "crpc.json"
    if raw_crpc_path.exists():
        raw_crpc = json.load(open(raw_crpc_path, encoding='utf-8'))
        processed_crpc = []
        for i, item in enumerate(raw_crpc):
            section_num = str(item.get('section', i))
            processed_crpc.append({
                "id": f"crpc_section_{section_num}",
                "type": "crpc",
                "chapter": item.get('chapter'),
                "chapter_title": item.get('chapter_title', ''),
                "section": section_num,
                "section_title": item.get('section_title', ''),
                "content": item.get('section_desc', ''),
                "metadata": {
                    "source": "Code of Criminal Procedure",
                    "chapter": item.get('chapter'),
                    "section": section_num
                }
            })
        json.dump(processed_crpc, open(data_dir / "crpc.json", 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        print(f"  ✓ Processed {len(processed_crpc)} CrPC sections")
    
    print("Processing Constitution...")
    raw_const_path = raw_dir / "constitution-of-india" / "constitution_of_india.json"
    if raw_const_path.exists():
        raw_const = json.load(open(raw_const_path, encoding='utf-8'))
        processed_const = []
        for i, item in enumerate(raw_const):
            article_num = str(item.get('article', i))
            processed_const.append({
                "id": f"constitution_article_{article_num}",
                "type": "constitution",
                "part": item.get('part'),
                "article": article_num,
                "title": item.get('article_title', ''),
                "content": item.get('article_desc', ''),
                "metadata": {
                    "source": "Constitution of India",
                    "part": item.get('part'),
                    "article": article_num
                }
            })
        json.dump(processed_const, open(data_dir / "constitution.json", 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        print(f"  ✓ Processed {len(processed_const)} Constitution articles")
    
    print("Processing Evidence Act...")
    raw_iea_path = raw_dir / "Indian-Law-Penal-Code-Json" / "iea.json"
    if raw_iea_path.exists():
        raw_iea = json.load(open(raw_iea_path, encoding='utf-8'))
        processed_iea = []
        for i, item in enumerate(raw_iea):
            section_num = str(item.get('section', i))
            processed_iea.append({
                "id": f"iea_section_{section_num}",
                "type": "evidence",
                "chapter": item.get('chapter'),
                "chapter_title": item.get('chapter_title', ''),
                "section": section_num,
                "section_title": item.get('section_title', ''),
                "content": item.get('section_desc', ''),
                "metadata": {
                    "source": "Indian Evidence Act",
                    "chapter": item.get('chapter'),
                    "section": section_num
                }
            })
        json.dump(processed_iea, open(data_dir / "evidence.json", 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        print(f"  ✓ Processed {len(processed_iea)} Evidence Act sections")
    
    print("Processing other acts...")
    acts = []
    act_files = [
        ("cpc.json", "Code of Civil Procedure", "cpc"),
        ("hma.json", "Hindu Marriage Act", "hma"),
        ("ida.json", "Indian Divorce Act", "ida"),
        ("MVA.json", "Motor Vehicles Act", "mva"),
        ("nia.json", "Negotiable Instruments Act", "nia")
    ]
    
    for filename, act_name, act_type in act_files:
        raw_act_path = raw_dir / "Indian-Law-Penal-Code-Json" / filename
        if raw_act_path.exists():
            raw_act = json.load(open(raw_act_path, encoding='utf-8'))
            for i, item in enumerate(raw_act):
                section = str(item.get('section', item.get('Section', i)))
                acts.append({
                    "id": f"{act_type}_section_{section}",
                    "type": act_type,
                    "chapter": item.get('chapter'),
                    "chapter_title": item.get('chapter_title', ''),
                    "section": section,
                    "section_title": item.get('section_title', ''),
                    "content": item.get('section_desc', ''),
                    "metadata": {
                        "source": act_name,
                        "chapter": item.get('chapter'),
                        "section": section
                    }
                })
            print(f"  ✓ Processed {len(raw_act)} sections from {act_name}")
    
    json.dump(acts, open(data_dir / "acts.json", 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print(f"\n✓ All data restored and processed successfully!")

if __name__ == "__main__":
    restore_data()
