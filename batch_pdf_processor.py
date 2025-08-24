import fitz  # PyMuPDF
import os
import json
import re
from PIL import Image
import io
import base64
import hashlib
import time
from datetime import datetime
from pathlib import Path
import argparse

class BatchPDFProcessor:
    def __init__(self, books_folder: str):
        self.books_folder = books_folder
        self.processed_data = {
            "books": {},
            "summary": {
                "total_books": 0,
                "total_pages": 0,
                "total_text_chunks": 0,
                "total_images": 0,
                "total_code_blocks": 0,
                "total_words": 0,
                "total_characters": 0,
                "processing_time": 0,
                "processed_at": ""
            }
        }
    
    def get_pdf_files(self):
        """Get all PDF files from the books folder"""
        pdf_files = []
        for file in os.listdir(self.books_folder):
            if file.lower().endswith('.pdf'):
                pdf_files.append(file)
        return sorted(pdf_files)
    
    def extract_text_from_pdf(self, pdf_path: str, book_name: str):
        """Extract text from a single PDF"""
        text_chunks = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Split text into chunks (roughly 500 characters each)
                chunks = self._split_text_into_chunks(text, 500)
                
                for i, chunk in enumerate(chunks):
                    if chunk.strip():
                        text_chunks.append({
                            "page": page_num + 1,
                            "chunk_id": i,
                            "text": chunk.strip(),
                            "type": "text",
                            "word_count": len(chunk.split()),
                            "char_count": len(chunk),
                            "book_name": book_name
                        })
            
            doc.close()
            return text_chunks
            
        except Exception as e:
            print(f"Error extracting text from {book_name}: {e}")
            return []
    
    def extract_images_from_pdf(self, pdf_path: str, book_name: str):
        """Extract images from a single PDF"""
        images = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                            img_hash = hashlib.md5(img_data).hexdigest()
                            
                            images.append({
                                "page": page_num + 1,
                                "image_index": img_index,
                                "image_hash": img_hash,
                                "size": len(img_data),
                                "format": "png",
                                "type": "image",
                                "width": pix.width,
                                "height": pix.height,
                                "colorspace": pix.colorspace.name if pix.colorspace else "unknown",
                                "has_alpha": pix.alpha > 0,
                                "book_name": book_name
                            })
                        
                        pix = None
                    except Exception as e:
                        print(f"Error extracting image on page {page_num + 1} from {book_name}: {e}")
            
            doc.close()
            return images
            
        except Exception as e:
            print(f"Error extracting images from {book_name}: {e}")
            return []
    
    def extract_code_blocks_from_pdf(self, pdf_path: str, book_name: str):
        """Extract code blocks from a single PDF"""
        code_blocks = []
        code_patterns = [
            r'```[\w]*\n(.*?)\n```',  # Markdown code blocks
            r'`([^`]+)`',  # Inline code
            r'(def\s+\w+\s*\([^)]*\):.*?)(?=\n\S|\Z)',  # Python functions
            r'(import\s+[\w\s,]+)',  # Import statements
            r'(class\s+\w+.*?)(?=\n\S|\Z)',  # Class definitions
            r'(function\s+\w+.*?)(?=\n\S|\Z)',  # JavaScript functions
            r'(public\s+class\s+\w+.*?)(?=\n\S|\Z)',  # Java classes
            r'(#include\s+[<"].*?[>"])',  # C/C++ includes
            r'(print\s*\(.*?\))',  # Print statements
            r'(return\s+.*?;)',  # Return statements
        ]
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Split text into chunks for code detection
                chunks = self._split_text_into_chunks(text, 1000)
                
                for chunk_id, chunk in enumerate(chunks):
                    for pattern in code_patterns:
                        matches = re.finditer(pattern, chunk, re.DOTALL | re.MULTILINE)
                        for match in matches:
                            code_text = match.group(1) if len(match.groups()) > 0 else match.group(0)
                            if len(code_text.strip()) > 10:  # Only significant code blocks
                                
                                # Detect programming language
                                language = self._detect_language(code_text)
                                
                                code_blocks.append({
                                    "page": page_num + 1,
                                    "chunk_id": chunk_id,
                                    "code": code_text.strip(),
                                    "type": "code",
                                    "language": language,
                                    "line_count": len(code_text.split('\n')),
                                    "char_count": len(code_text),
                                    "has_functions": bool(re.search(r'def\s+\w+|function\s+\w+', code_text)),
                                    "has_imports": bool(re.search(r'import\s+|#include\s+', code_text)),
                                    "book_name": book_name
                                })
            
            doc.close()
            return code_blocks
            
        except Exception as e:
            print(f"Error extracting code from {book_name}: {e}")
            return []
    
    def _detect_language(self, code_text):
        """Detect programming language from code snippet"""
        code_lower = code_text.lower()
        
        if re.search(r'def\s+\w+|import\s+|print\s*\(', code_lower):
            return "python"
        elif re.search(r'function\s+\w+|var\s+|let\s+|const\s+', code_lower):
            return "javascript"
        elif re.search(r'public\s+class|System\.out|import\s+java', code_lower):
            return "java"
        elif re.search(r'#include\s+|int\s+main|printf\s*\(', code_lower):
            return "c/c++"
        elif re.search(r'<?php|echo\s+', code_lower):
            return "php"
        elif re.search(r'def\s+\w+|puts\s+', code_lower):
            return "ruby"
        else:
            return "unknown"
    
    def _split_text_into_chunks(self, text, chunk_size):
        """Split text into chunks of approximately chunk_size characters"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) + 1 > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def extract_metadata_from_pdf(self, pdf_path: str, book_name: str):
        """Extract metadata from a single PDF"""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            pdf_metadata = {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "pages": len(doc),
                "file_size": os.path.getsize(pdf_path),
                "extraction_date": str(fitz.get_pdf_now()),
                "pdf_version": getattr(doc, 'version', 'unknown'),
                "book_name": book_name
            }
            
            doc.close()
            return pdf_metadata
            
        except Exception as e:
            print(f"Error extracting metadata from {book_name}: {e}")
            return {
                "title": "",
                "author": "",
                "subject": "",
                "creator": "",
                "producer": "",
                "pages": 0,
                "file_size": 0,
                "extraction_date": str(fitz.get_pdf_now()),
                "pdf_version": "unknown",
                "book_name": book_name
            }
    
    def process_single_pdf(self, pdf_file: str):
        """Process a single PDF file"""
        pdf_path = os.path.join(self.books_folder, pdf_file)
        book_name = pdf_file.replace('.pdf', '')
        
        print(f"📖 Processing: {pdf_file}")
        
        # Extract metadata
        metadata = self.extract_metadata_from_pdf(pdf_path, book_name)
        
        # Extract text
        text_chunks = self.extract_text_from_pdf(pdf_path, book_name)
        print(f"   📝 Extracted {len(text_chunks)} text chunks")
        
        # Extract images
        images = self.extract_images_from_pdf(pdf_path, book_name)
        print(f"   🖼️  Extracted {len(images)} images")
        
        # Extract code blocks
        code_blocks = self.extract_code_blocks_from_pdf(pdf_path, book_name)
        print(f"   💻 Extracted {len(code_blocks)} code blocks")
        
        # Store book data
        self.processed_data["books"][book_name] = {
            "metadata": metadata,
            "text_chunks": text_chunks,
            "images": images,
            "code_blocks": code_blocks,
            "summary": {
                "total_pages": metadata["pages"],
                "total_text_chunks": len(text_chunks),
                "total_images": len(images),
                "total_code_blocks": len(code_blocks),
                "total_words": sum(chunk.get("word_count", 0) for chunk in text_chunks),
                "total_characters": sum(chunk.get("char_count", 0) for chunk in text_chunks)
            }
        }
        
        return len(text_chunks), len(images), len(code_blocks)
    
    def process_all_pdfs(self):
        """Process all PDF files in the books folder"""
        start_time = time.time()
        
        pdf_files = self.get_pdf_files()
        total_files = len(pdf_files)
        
        print(f"🚀 Starting batch processing of {total_files} PDF files...")
        print("="*60)
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{total_files}] Processing: {pdf_file}")
            
            try:
                text_count, image_count, code_count = self.process_single_pdf(pdf_file)
                
                # Update summary
                self.processed_data["summary"]["total_books"] += 1
                self.processed_data["summary"]["total_text_chunks"] += text_count
                self.processed_data["summary"]["total_images"] += image_count
                self.processed_data["summary"]["total_code_blocks"] += code_count
                
                # Get total pages from metadata
                book_name = pdf_file.replace('.pdf', '')
                if book_name in self.processed_data["books"]:
                    pages = self.processed_data["books"][book_name]["metadata"]["pages"]
                    self.processed_data["summary"]["total_pages"] += pages
                
                print(f"   ✅ Completed: {text_count} text, {image_count} images, {code_count} code blocks")
                
            except Exception as e:
                print(f"   ❌ Error processing {pdf_file}: {e}")
                continue
        
        # Calculate final summary
        end_time = time.time()
        processing_time = end_time - start_time
        
        self.processed_data["summary"]["processing_time"] = processing_time
        self.processed_data["summary"]["processed_at"] = datetime.now().isoformat()
        
        # Calculate total words and characters
        total_words = 0
        total_chars = 0
        for book_data in self.processed_data["books"].values():
            total_words += book_data["summary"]["total_words"]
            total_chars += book_data["summary"]["total_characters"]
        
        self.processed_data["summary"]["total_words"] = total_words
        self.processed_data["summary"]["total_characters"] = total_chars
        
        print("\n" + "="*60)
        print("🎉 BATCH PROCESSING COMPLETED!")
        print("="*60)
        self.print_summary()
    
    def print_summary(self):
        """Print processing summary"""
        summary = self.processed_data["summary"]
        
        print(f"📊 PROCESSING SUMMARY:")
        print(f"   Total books processed: {summary['total_books']}")
        print(f"   Total pages: {summary['total_pages']:,}")
        print(f"   Total text chunks: {summary['total_text_chunks']:,}")
        print(f"   Total images: {summary['total_images']:,}")
        print(f"   Total code blocks: {summary['total_code_blocks']:,}")
        print(f"   Total words: {summary['total_words']:,}")
        print(f"   Total characters: {summary['total_characters']:,}")
        print(f"   Processing time: {summary['processing_time']:.2f} seconds")
        print(f"   Average time per book: {summary['processing_time']/summary['total_books']:.2f} seconds")
        
        # Show top books by content
        print(f"\n📚 TOP BOOKS BY CONTENT:")
        book_summaries = []
        for book_name, book_data in self.processed_data["books"].items():
            book_summary = book_data["summary"]
            book_summaries.append({
                "name": book_name,
                "pages": book_summary["total_pages"],
                "text_chunks": book_summary["total_text_chunks"],
                "images": book_summary["total_images"],
                "code_blocks": book_summary["total_code_blocks"],
                "words": book_summary["total_words"]
            })
        
        # Sort by word count
        book_summaries.sort(key=lambda x: x["words"], reverse=True)
        
        for i, book in enumerate(book_summaries[:10], 1):
            print(f"   {i}. {book['name']}: {book['words']:,} words, {book['pages']} pages")
    
    def save_processed_data(self, output_file: str):
        """Save processed data to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.processed_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Processed data saved to: {output_file}")
    
    def create_rag_ready_data(self, output_file: str):
        """Create RAG-ready data format"""
        rag_data = {
            "text_chunks": [],
            "images": [],
            "code_blocks": [],
            "metadata": {},
            "summary": self.processed_data["summary"]
        }
        
        # Combine all text chunks
        for book_name, book_data in self.processed_data["books"].items():
            for chunk in book_data["text_chunks"]:
                rag_data["text_chunks"].append({
                    "page": chunk["page"],
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "type": "text",
                    "word_count": chunk["word_count"],
                    "char_count": chunk["char_count"],
                    "book_name": chunk["book_name"]
                })
        
        # Combine all images
        for book_name, book_data in self.processed_data["books"].items():
            for img in book_data["images"]:
                rag_data["images"].append({
                    "page": img["page"],
                    "image_index": img["image_index"],
                    "image_hash": img["image_hash"],
                    "size": img["size"],
                    "format": img["format"],
                    "type": "image",
                    "width": img["width"],
                    "height": img["height"],
                    "colorspace": img["colorspace"],
                    "has_alpha": img["has_alpha"],
                    "book_name": img["book_name"]
                })
        
        # Combine all code blocks
        for book_name, book_data in self.processed_data["books"].items():
            for code in book_data["code_blocks"]:
                rag_data["code_blocks"].append({
                    "page": code["page"],
                    "chunk_id": code["chunk_id"],
                    "code": code["code"],
                    "type": "code",
                    "language": code["language"],
                    "line_count": code["line_count"],
                    "char_count": code["char_count"],
                    "has_functions": code["has_functions"],
                    "has_imports": code["has_imports"],
                    "book_name": code["book_name"]
                })
        
        # Save RAG-ready data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rag_data, f, indent=2, ensure_ascii=False)
        print(f"🤖 RAG-ready data saved to: {output_file}")

def main():
    # Resolve books folder
    script_dir = Path(__file__).resolve().parent
    default_books_dir = script_dir / "books"

    parser = argparse.ArgumentParser(description="Batch process PDFs into text/images/code blocks for RAG")
    parser.add_argument(
        "--books",
        "--books-folder",
        dest="books_folder",
        default=str(default_books_dir),
        help="Path to the folder containing PDF books (default: ./books next to this script)",
    )
    args = parser.parse_args()

    # Try provided path, then common fallbacks
    candidate_dirs = [
        Path(args.books_folder).expanduser(),
        Path.cwd() / "books",
        default_books_dir,
    ]

    resolved_books_dir: str | None = None
    for candidate in candidate_dirs:
        if candidate.exists() and candidate.is_dir():
            resolved_books_dir = str(candidate)
            break

    if not resolved_books_dir:
        tried = "\n  - ".join(str(p) for p in candidate_dirs)
        print(f"Error: books folder not found! Tried:\n  - {tried}")
        return

    processor = BatchPDFProcessor(resolved_books_dir)
    
    try:
        # Process all PDFs
        processor.process_all_pdfs()
        
        # Save detailed data
        processor.save_processed_data("all_books_data.json")
        
        # Create RAG-ready data
        processor.create_rag_ready_data("rag_ready_data.json")
        
        print("\n✅ Batch processing completed successfully!")
        print("📁 Files created:")
        print("   - all_books_data.json (detailed data for each book)")
        print("   - rag_ready_data.json (RAG-ready format)")
        
    except Exception as e:
        print(f"Error during batch processing: {e}")

if __name__ == "__main__":
    main() 