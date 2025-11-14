"""
OpenAI service - Business logic for document text extraction using GPT-4o-mini.
"""

import os
import base64
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy.orm import Session
from openai import OpenAI

from app.config import settings
from app.models.document import Document


class OpenAIService:
    """Service class for OpenAI operations."""

    # Initialize OpenAI client
    _client: Optional[OpenAI] = None

    @classmethod
    def get_client(cls) -> OpenAI:
        """
        Get or create OpenAI client instance.

        Returns:
            OpenAI client
        """
        if cls._client is None:
            cls._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return cls._client

    @staticmethod
    def count_words(text: str) -> int:
        """
        Count words in text.

        Args:
            text: Text to count words in

        Returns:
            Number of words
        """
        if not text or text.strip() == "":
            return 0
        return len(text.split())

    @staticmethod
    def build_extraction_prompt(content: str, file_type: str) -> str:
        """
        Build prompt for GPT to extract text from document.

        Args:
            content: Raw file content (or base64 for binary)
            file_type: Type of file (pdf, docx)

        Returns:
            Prompt string
        """
        return f"""You are a document text extraction assistant.
Extract all text content from this {file_type.upper()} document.

Instructions:
- Extract ALL text content, maintaining structure where possible
- Remove formatting artifacts and metadata
- Keep paragraphs separated by newlines
- Do not add any commentary or explanation
- Return only the extracted text

Document content:
{content[:5000]}  # Limit to avoid token overflow
"""

    @staticmethod
    def call_gpt_for_extraction(content: str, file_type: str) -> str:
        """
        Call GPT-4o-mini to extract text from document.

        Args:
            content: Raw file content
            file_type: Type of file

        Returns:
            Extracted text

        Raises:
            Exception: If API call fails
        """
        client = OpenAIService.get_client()

        prompt = OpenAIService.build_extraction_prompt(content, file_type)

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise document text extraction assistant. Extract only the text content without any additional commentary."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=4000
            )

            extracted_text = response.choices[0].message.content
            return extracted_text

        except Exception as e:
            raise Exception(f"GPT extraction failed: {str(e)}")

    @staticmethod
    def extract_text_from_file(file_path: str, file_type: str) -> Dict:
        """
        Extract text from file based on type.

        Args:
            file_path: Path to file
            file_type: Type of file (txt, pdf, docx)

        Returns:
            Dict with full_text, word_count, page_count

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type not supported
        """
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Validate file type
        if file_type not in ['txt', 'pdf', 'docx', 'doc']:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Extract based on type
        if file_type == 'txt':
            # Simple text file - read directly
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    full_text = f.read()

                word_count = OpenAIService.count_words(full_text)
                page_count = max(1, len(full_text) // 3000)  # Estimate: ~3000 chars per page

                return {
                    'full_text': full_text,
                    'word_count': word_count,
                    'page_count': page_count
                }
            except UnicodeDecodeError:
                # Try with different encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    full_text = f.read()

                word_count = OpenAIService.count_words(full_text)
                page_count = max(1, len(full_text) // 3000)

                return {
                    'full_text': full_text,
                    'word_count': word_count,
                    'page_count': page_count
                }

        elif file_type in ['pdf', 'docx', 'doc']:
            # Binary files - use GPT for extraction
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()

                # Convert to base64 for GPT (or read as text if possible)
                content_preview = file_content[:10000].decode('utf-8', errors='ignore')

                # Call GPT to extract text
                extracted_text = OpenAIService.call_gpt_for_extraction(content_preview, file_type)

                word_count = OpenAIService.count_words(extracted_text)
                page_count = max(1, word_count // 500)  # Estimate: ~500 words per page

                return {
                    'full_text': extracted_text,
                    'word_count': word_count,
                    'page_count': page_count
                }
            except Exception as e:
                raise Exception(f"Failed to extract from {file_type}: {str(e)}")

    @staticmethod
    async def process_document(document_id: str, db: Session) -> None:
        """
        Process a document: extract text and update database.

        Args:
            document_id: Document UUID
            db: Database session
        """
        try:
            # Get document
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return

            # Update status to processing
            document.status = 'processing'
            db.commit()

            # Extract text
            try:
                result = OpenAIService.extract_text_from_file(
                    document.file_path,
                    document.file_type
                )

                # Update document with extracted data
                document.full_text = result['full_text']
                document.word_count = result['word_count']
                document.page_count = result['page_count']
                document.status = 'ready'

            except Exception as e:
                # Mark as failed
                document.status = 'failed'
                print(f"Error processing document {document_id}: {str(e)}")

            db.commit()

        except Exception as e:
            print(f"Error in process_document: {str(e)}")

    @staticmethod
    async def process_pending_documents(db: Session) -> None:
        """
        Process all pending documents in the database.

        Args:
            db: Database session
        """
        # Get all pending documents
        pending_docs = db.query(Document).filter(Document.status == 'pending').all()

        # Process each document
        for doc in pending_docs:
            await OpenAIService.process_document(doc.id, db)
