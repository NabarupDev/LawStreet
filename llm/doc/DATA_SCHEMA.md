# Legal Data JSON Schema Specification

## Purpose
This document defines the exact structure for legal document JSON files used in the RAG system.

---

## Schema Definition

### Top-Level Structure
All JSON files must contain an array of legal document objects:

```json
[
  {legal_document_object_1},
  {legal_document_object_2},
  ...
]
```

---

## Legal Document Object Schema

### Required Fields

#### `id` (string)
- **Type**: string
- **Description**: Unique identifier for the document
- **Format**: `{act}_{section_number}` or `{act}_article_{article_number}`
- **Examples**: 
  - `"ipc_420"`
  - `"ipc_302"`
  - `"constitution_article_21"`
  - `"crpc_41"`
  - `"evidence_24"`
- **Requirements**:
  - Must be unique across the entire dataset
  - Should be stable (same document = same ID across updates)
  - Only alphanumeric and underscore characters
  - No spaces or special characters
- **Edge Cases**:
  - For sections with letters: `"ipc_376a"`, `"ipc_376b"`
  - For sub-sections: `"ipc_304_2"` (Section 304(2))
  - For ranges: `"ipc_141_149"` (Sections 141-149 grouped)

---

#### `act` (string)
- **Type**: string
- **Description**: Abbreviated name of the legal act
- **Allowed Values**:
  - `"IPC"` - Indian Penal Code
  - `"CrPC"` - Code of Criminal Procedure
  - `"Constitution"` - Constitution of India
  - `"Evidence Act"` - Indian Evidence Act
  - `"CPC"` - Code of Civil Procedure
  - `"HMA"` - Hindu Marriage Act
  - `"MVA"` - Motor Vehicles Act
  - `"NIA"` - Negotiable Instruments Act
  - `"IDA"` - Indian Divorce Act
  - Custom act names (format: Title Case, no abbreviation exceeds 10 chars)
- **Examples**: `"IPC"`, `"Constitution"`, `"CrPC"`
- **Requirements**: Must match one of the standard values or be consistently used

---

#### `section` (string) OR `article` (string)
- **Type**: string (not integer - preserve leading zeros and letters)
- **Description**: Section number (for acts) or Article number (for Constitution)
- **Field Name**:
  - Use `"section"` for: IPC, CrPC, Evidence Act, other acts
  - Use `"article"` for: Constitution of India only
- **Examples**:
  - Section: `"420"`, `"302"`, `"376A"`, `"509"`, `"1"`
  - Article: `"21"`, `"14"`, `"356"`, `"1"`
- **Format Rules**:
  - String type to preserve: `"007"`, `"02"`, `"123A"`
  - May include letters: `"376A"`, `"376B"`, `"124A"`
  - May include parentheses for sub-sections: `"304(2)"` or just `"304_2"`
- **Edge Cases**:
  - Missing section: Use `"0"` or `"NA"` (avoid empty string)
  - Preamble or general provisions: Use `"Preamble"` or `"General"`

---

#### `title` (string)
- **Type**: string
- **Description**: Human-readable title or heading of the section/article
- **Examples**:
  - `"Cheating and dishonestly inducing delivery of property"`
  - `"Murder"`
  - `"Right to equality"`
  - `"Arrest how made"`
- **Format**: Title Case recommended (but not enforced)
- **Maximum Length**: 200 characters (recommended)
- **Edge Cases**:
  - If no title available: Use `""` (empty string) or summary of first line
  - Long titles: Do not truncate, store full title

---

#### `content` (string)
- **Type**: string
- **Description**: Full text of the legal provision
- **Examples**:
  ```
  "Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, or to make, alter or destroy the whole or any part of a valuable security, or anything which is signed or sealed, and which is capable of being converted into a valuable security, shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine."
  ```
- **Format**: Plain text, preserve original formatting
- **Maximum Length**: No limit (can be several paragraphs)
- **Newlines**: Use `\n` for paragraph breaks
- **Edge Cases**:
  - Very long provisions (1000+ words): Store in full, chunking happens during indexing
  - Empty content: Use `"Content not available"` or `"[Text missing]"`
  - Content with special characters: Properly escape JSON (quotes, backslashes)

---

#### `type` (string)
- **Type**: string
- **Description**: Category/type of legal document
- **Allowed Values**:
  - `"ipc"` - Indian Penal Code section
  - `"constitution"` - Constitutional article
  - `"crpc"` - Criminal procedure section
  - `"evidence"` - Evidence Act section
  - `"cpc"` - Civil procedure section
  - `"act"` - Other acts
- **Examples**: `"ipc"`, `"constitution"`, `"crpc"`
- **Format**: Lowercase, no spaces
- **Usage**: Used for filtering and categorization in retrieval

---

### Optional Fields

#### `meta` (object)
- **Type**: object (nested JSON object)
- **Description**: Additional metadata about the provision
- **Fields** (all optional within meta):

  - `year_enacted` (string): Year the provision was enacted
    - Example: `"1860"`, `"1950"`, `"1973"`
    - Format: 4-digit year as string
  
  - `last_amended` (string): Date or year of last amendment
    - Example: `"2013"`, `"2018-07-01"`
    - Format: YYYY or YYYY-MM-DD
  
  - `source_url` (string): Official URL to the legal text
    - Example: `"https://legislative.gov.in/..."`
    - Format: Valid HTTP/HTTPS URL
  
  - `notes` (string): Additional context or explanatory notes
    - Example: `"This section was amended by Act 13 of 2013"`
    - Format: Free text, max 500 characters recommended
  
  - `status` (string): Current status of provision
    - Values: `"active"`, `"repealed"`, `"amended"`, `"obsolete"`
    - Default: `"active"`
  
  - `tags` (array of strings): Keywords for categorization
    - Example: `["property crime", "imprisonment", "fine"]`
    - Format: Array of lowercase keyword strings

- **Example**:
  ```json
  "meta": {
    "year_enacted": "1860",
    "last_amended": "2013",
    "source_url": "https://legislative.gov.in/ipc",
    "notes": "Frequently invoked in cybercrime cases",
    "status": "active",
    "tags": ["cheating", "fraud", "property crime"]
  }
  ```

---

#### `chapter` (integer or string)
- **Type**: integer or string
- **Description**: Chapter number the section belongs to
- **Examples**: `1`, `4`, `"IVA"`, `"23"`
- **Usage**: For organizing sections by chapter

---

#### `chapter_title` (string)
- **Type**: string
- **Description**: Title/name of the chapter
- **Examples**: 
  - `"General Exceptions"`
  - `"Of Offences Against The State"`
  - `"Of Arrests"`
- **Format**: Title Case

---

#### `offense` (string)
- **Type**: string
- **Description**: Type or nature of offense (for criminal law)
- **Examples**:
  - `"Cheating"`
  - `"Murder"`
  - `"Theft"`
  - `"Assault"`
- **Usage**: Specific to IPC and criminal provisions

---

#### `punishment` (string)
- **Type**: string
- **Description**: Punishment prescribed for the offense
- **Examples**:
  - `"Imprisonment up to 7 years and fine"`
  - `"Death or life imprisonment"`
  - `"Fine up to Rs. 10,000"`
- **Format**: Free text description
- **Usage**: Specific to criminal law sections

---

## Complete Example Documents

### Example 1: IPC Section (Full Schema)
```json
{
  "id": "ipc_420",
  "act": "IPC",
  "section": "420",
  "title": "Cheating and dishonestly inducing delivery of property",
  "content": "Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, or to make, alter or destroy the whole or any part of a valuable security, or anything which is signed or sealed, and which is capable of being converted into a valuable security, shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine.",
  "type": "ipc",
  "chapter": 17,
  "chapter_title": "Of Offences Against Property",
  "offense": "Cheating and dishonestly inducing delivery of property",
  "punishment": "Imprisonment up to 7 years and fine",
  "meta": {
    "year_enacted": "1860",
    "last_amended": "2013",
    "source_url": "https://legislative.gov.in/sites/default/files/A1860-45.pdf",
    "notes": "Commonly known as '420 case' in popular culture",
    "status": "active",
    "tags": ["cheating", "fraud", "property crime", "cognizable", "non-bailable"]
  }
}
```

### Example 2: Constitution Article (Minimal Schema)
```json
{
  "id": "constitution_article_21",
  "act": "Constitution",
  "article": "21",
  "title": "Protection of life and personal liberty",
  "content": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
  "type": "constitution"
}
```

### Example 3: CrPC Section
```json
{
  "id": "crpc_41",
  "act": "CrPC",
  "section": "41",
  "title": "When police may arrest without warrant",
  "content": "Any police officer may without an order from a Magistrate and without a warrant, arrest any person—(a) who has been concerned in any cognizable offence...",
  "type": "crpc",
  "chapter": 5,
  "chapter_title": "Arrest of Persons",
  "meta": {
    "year_enacted": "1973",
    "source_url": "https://legislative.gov.in/crpc"
  }
}
```

---

## Chunking Impact on Schema

**IMPORTANT**: During indexing, documents are split into chunks. Each chunk gets additional metadata:

### Chunk Metadata (added during indexing)
```json
{
  "original_id": "ipc_420",        // Original document ID before chunking
  "chunk_index": 0,                // Which chunk (0-based)
  "chunk_total": 3,                // Total chunks for this document
  // ... all original metadata preserved ...
}
```

### Chunk ID Format
```
{original_id}_{chunk_index}
```

**Examples**:
- `"ipc_420_0"` - First chunk of IPC Section 420
- `"ipc_420_1"` - Second chunk of IPC Section 420
- `"constitution_article_21_0"` - Constitution Article 21 (single chunk)

---

## Validation Rules

### Required Field Validation
1. `id` must be present and non-empty
2. `act` must be present
3. Either `section` OR `article` must be present
4. `title` can be empty but must be present
5. `content` must be present (can be "[Missing]" if unavailable)
6. `type` must be present

### Data Type Validation
1. All string fields: Trim whitespace
2. All string fields: No null values (use "" for missing)
3. `meta` object: Can be empty `{}` or omitted
4. `chapter`: If present, must be integer or string
5. Arrays (like tags): Can be empty `[]` but must be array type

### Content Quality Rules
1. No HTML tags in content (plain text only)
2. Preserve original legal language (no paraphrasing)
3. Use consistent terminology across documents
4. Ensure proper JSON escaping for quotes and special chars

---

## Usage in Indexing

The indexing script (`scripts/index_data.py`) will:

1. **Load** these JSON files
2. **Validate** against this schema
3. **Chunk** long content fields (800 char chunks, 200 char overlap)
4. **Generate** stable IDs for each chunk
5. **Embed** each chunk using sentence-transformers
6. **Store** in ChromaDB with all metadata preserved

---

## Adding New Data

### For a New Act/Document Type:

1. Create JSON file: `Data/new_act.json`
2. Follow schema above
3. Choose appropriate `act` abbreviation
4. Set consistent `type` value
5. Update `app/config.py` to include new file in `DATA_FILES`
6. Run: `python scripts/index_data.py`

### For Updating Existing Documents:

1. Modify JSON file in `Data/` folder
2. Keep same `id` values (ensures updates, not duplicates)
3. Run: `python scripts/index_data.py`
4. Script will replace old chunks with new ones (same IDs)

---

## Notes

- **Backwards Compatibility**: If adding new fields, existing documents without those fields will still work
- **Future Extensions**: Schema can be extended with new optional fields without breaking existing data
- **Type Safety**: Ensure consistent types across documents (don't mix string/int for same field)

---

**Schema Version**: 1.0.0  
**Last Updated**: November 15, 2025
