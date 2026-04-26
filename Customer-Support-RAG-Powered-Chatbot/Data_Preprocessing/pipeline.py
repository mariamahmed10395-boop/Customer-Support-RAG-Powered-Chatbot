"""
Customer Support RAG Pipeline Runner
====================================
This file is responsible for executing all RAG preprocessing steps.
It acts as a bridge between the Preprocessor class and the Application (UI/Server).
"""

# Import your professional class
try:
    from .preprocess import CustomerDataPreprocessor
except ImportError:
    from preprocess import CustomerDataPreprocessor

def run_customer_pipeline(file_path):
    """
    This function executes the full RAG preprocessing pipeline.

    Parameters:
    file_path (str): Path to the customer support CSV file.

    Returns:
    pandas.DataFrame: The final processed dataset containing 'context' chunks.
    """

    # 1. Initialize the preprocessor object
    pipeline = CustomerDataPreprocessor(file_path)

    # 2. Execute preprocessing steps in sequence (Method Chaining)
    # Notice: We follow the specific steps for NLP/RAG
    (pipeline.load_data()
             .clean_data()
             .process_texts()
             .build_knowledge_chunks())

    # 3. Retrieve the final dataset
    df_final = pipeline.df_processed

    print("\n[SUCCESS] RAG Pipeline executed successfully!")
    print(f"[INFO] Final Knowledge Base Size: {len(df_final)} entries.")

    return df_final


if __name__ == "__main__":
    # Update this path to your actual CSV file location
    DATA_PATH = r'C:\Users\modern\OneDrive\Desktop\Customer-Support-RAG-Powered-Chatbot\Customer-Support-RAG-Powered-Chatbot\Data_Preprocessing\customer_support_data.csv'
    
    # Run the pipeline
    final_data = run_customer_pipeline(DATA_PATH)
    
    # Display sample to verify
    print("\n--- Sample of Processed Knowledge (Context) ---")
    print(final_data['context'].head(2).values)