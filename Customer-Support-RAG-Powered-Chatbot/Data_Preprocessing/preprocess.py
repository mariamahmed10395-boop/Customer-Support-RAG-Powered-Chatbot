"""
Customer Support RAG Pipeline
=============================
This module contains the CustomerDataPreprocessor class.

Responsibilities:
- Load raw customer support CSV data.
- Clean and deduplicate Q&A pairs.
- Normalize text (lowercase, placeholder replacement).
- Construct knowledge chunks for RAG embedding.
- Export processed dataset for the Vector Engine.
"""

import pandas as pd
import re
import os

class CustomerDataPreprocessor:
    """
    Pipeline class to process Customer Support dataset step by step.
    """

    def __init__(self, file_path):
        """
        Initialize pipeline with dataset path.
        """
        self.file_path = file_path
        self.df = None
        self.df_processed = None

    def load_data(self):
        """
        Load dataset from CSV file and validate existence.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Path not found: {self.file_path}")

        self.df = pd.read_csv(self.file_path, low_memory=False)
        
        if self.df is None or self.df.empty:
            raise ValueError("Dataset failed to load or is empty.")

        print(f"[INFO] Initial Shape: {self.df.shape}")
        return self

    def clean_data(self):
        """
        Clean dataset and remove low-quality entries.
        
        Steps:
        - Drop rows with missing core fields.
        - Remove duplicate instructions to prevent redundant embeddings.
        """
        initial_count = len(self.df)
        
        # Drop Nulls in essential columns
        self.df.dropna(subset=['instruction', 'response', 'intent'], inplace=True)
        
        # Remove duplicates based on the question (instruction)
        self.df.drop_duplicates(subset=['instruction'], keep='first', inplace=True)
        
        final_count = len(self.df)
        print(f"[INFO] Cleaning completed. Removed {initial_count - final_count} rows.")
        print(f"[INFO] Current Shape: {self.df.shape}")
        return self

    def _normalize_text(self, text):
        """
        Internal helper for text standardization.
        """
        if not isinstance(text, str):
            return ""
            
        text = text.lower()
        # Handle placeholders to make them more descriptive for the LLM
        text = text.replace("{{order number}}", "[order_number]")
        text = text.replace("{{refund amount}}", "[refund_amount]")
        text = text.replace("{{customer name}}", "[customer_name]")
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def process_texts(self):
        """
        Apply normalization and clean up categories/intents.
        """
        # Normalize main text columns
        self.df['instruction'] = self.df['instruction'].apply(self._normalize_text)
        self.df['response'] = self.df['response'].apply(self._normalize_text)
        
        # Standardize categories and intents (uppercase/strip)
        if 'category' in self.df.columns:
            self.df['category'] = self.df['category'].str.strip().str.upper()
        self.df['intent'] = self.df['intent'].str.strip().str.lower()
        
        print("[INFO] Text normalization and field standardization completed.")
        return self

    def build_knowledge_chunks(self):
        """
        Engineer the 'context' feature for the RAG system.
        This merges intent, question, and answer into a single searchable unit.
        """
        self.df['context'] = (
            "Intent: " + self.df['intent'] + 
            " | Category: " + (self.df['category'] if 'category' in self.df.columns else "N/A") +
            " | Question: " + self.df['instruction'] + 
            " | Answer: " + self.df['response']
        )
        
        self.df_processed = self.df
        print("[INFO] Knowledge chunks successfully constructed.")
        return self

    def save_processed_data(self, output_path='processed_support_data.csv'):
        """
        Export the final dataset to CSV format.
        """
        if self.df_processed is not None:
            self.df_processed.to_csv(output_path, index=False)
            print(f"[SUCCESS] Processed data saved to: {output_path}")
        else:
            print("[ERROR] No processed data available to save.")

# --- Execution ---
if __name__ == "__main__":
    DATA_FILE = r'C:\Users\modern\OneDrive\Desktop\Customer-Support-RAG-Powered-Chatbot\Customer-Support-RAG-Powered-Chatbot\Data_Preprocessing\customer_support_data.csv'
    
    pipeline = CustomerDataPreprocessor(DATA_FILE)
    
    pipeline.load_data() \
            .clean_data() \
            .process_texts() \
            .build_knowledge_chunks() \
            .save_processed_data()