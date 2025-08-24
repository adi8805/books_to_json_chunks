
# 📚 Batch PDF Processor

A comprehensive Python utility for **batch processing PDFs** — extracting **text**, **images**, **code blocks**, and **metadata** — and generating **RAG-ready datasets** for AI pipelines, NLP projects, or archival purposes.

---

## 📌 Features

- 📝 **Text Extraction**  
  Splits PDF content into clean text chunks with word and character counts.

- 🖼 **Image Extraction**  
  Detects and extracts embedded images with metadata like size, resolution, and color space.

- 💻 **Code Detection**  
  Identifies and extracts programming code blocks (Python, JavaScript, Java, C/C++, PHP, Ruby, etc.).

- 📊 **Detailed Summary**  
  Generates per-book and overall statistics, including total pages, word counts, and processing time.

- 🤖 **RAG-Ready Output**  
  Creates a structured JSON dataset for **Retrieval-Augmented Generation** or other AI workflows.

- ⚡ **Fast & Scalable**  
  Optimized for processing **hundreds of PDFs** efficiently.

---

## 📥 Installation

Ensure you have **Python 3.8+** installed.  
Clone the repository and install the dependencies:

```bash
git clone https://github.com/adi8805/books_to_json_chunks
cd batch-pdf-processor
pip install -r requirements.txt
````

---

## ⚡ Usage

Place all your PDFs in a folder named `books` (or specify a custom folder).

Run the script:

```bash
python3 batch_pdf_processor.py
```

Custom books folder:

```bash
python3 batch_pdf_processor.py --books /path/to/your/pdf/folder
```

---

## 🖥 Example Output

```
🚀 Starting batch processing of 3 PDF files...
============================================================

[1/3] Processing: book1.pdf
📖 Processing: book1.pdf
   📝 Extracted 1,452 text chunks
   🖼️  Extracted 23 images
   💻 Extracted 5 code blocks
   ✅ Completed: 1452 text, 23 images, 5 code blocks

[2/3] Processing: book2.pdf
...
============================================================
🎉 BATCH PROCESSING COMPLETED!
============================================================
📊 PROCESSING SUMMARY:
   Total books processed: 3
   Total pages: 1,325
   Total text chunks: 5,232
   Total images: 87
   Total code blocks: 54
   Total words: 912,354
   Total characters: 5,023,210
   Processing time: 42.15 seconds
   Average time per book: 14.05 seconds
```

---

## 📂 Output Files

|File|Description|
|---|---|
|`all_books_data.json`|Detailed structured data for each book|
|`rag_ready_data.json`|Clean, merged data for AI pipelines (RAG, embeddings, etc.)|

---

## ⚙️ Configuration

|Variable|Description|Default|
|---|---|---|
|`books_folder`|Path to the folder containing PDF books|`./books`|
|`chunk_size`|Approx. character size per text chunk|`500`|
|`output_file`|Filename for saved JSON results|`all_books_data.json`|

---

## 📜 License

This project is licensed under the **MIT License**.  
Feel free to use, modify, and distribute.

---

## 🤝 Contributing

Contributions are welcome!

- Fork the repo
    
- Make your changes
    
- Submit a pull request
    

---

## ⚠️ Disclaimer

This tool is intended for **educational and research purposes**.  
Ensure you have the right to process any PDFs you use with this script.

---

## 💡 Future Enhancements

-  Parallel PDF processing for faster performance
    
-  OCR integration for scanned PDFs
    
-  Export in CSV or SQLite format
    
-  CLI for advanced configurations
