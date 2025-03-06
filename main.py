import os
import re
from pathlib import Path
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted text from the PDF, or an empty string on error.
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")  # Consider logging instead of printing
        return ""


def extract_process_number(text: str) -> Optional[str]:
    """
    Extract process number in the format NNNNNNN-NN.YYYY.N.NN.NNNN.

    Args:
        text: Text to search for process number.

    Returns:
        Process number if found, None otherwise.
    """
    pattern = r'\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def generate_timestamp() -> str:
    """
    Generate a timestamp string for use in filenames.

    Returns:
        Timestamp in format YYYYMMDD_HHMMSS.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def process_with_gemini(text_content: str, output_dir: Path, pdf_name: str,
                       process_number: Optional[str], api_key: str) -> str:
    """
    Process text content using Google Gemini API for first-stage analysis.

    Args:
        text_content: Text content to be processed.
        output_dir: Directory to save the output.
        pdf_name: Name of the original PDF file (for fallback filename).
        process_number: Process number if found, None otherwise.
        api_key: The API key to use for Gemini.

    Returns:
        The full response text for second-stage processing, or an empty
        string on error.  Returns an empty string if *any* error occurs.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")  # Consider model as parameter

        prompt = """Atue como um excelente assistente jurídico de um juiz federal. Liste os principais argumentos do recurso a seguir. Não use itens, tópicos, markdown ou bullet points. Não utilize \"o recurso\" alega, etc. Utilize o autor (a autora ou o INSS, a depender do caso, você deve determinar quem é o autor ou a autora do recurso) relata, afirma, alega, aduz, assinala, etc ... Não diga sentença monocrática, pois, sentença, por definição é monocrática. Ao mencionar decisão do juízo a quo, diga apenas sentença ou decisão recorrida. Não mencione o nome por extenso da parte autora. Inicie com \"Trata-se de recurso interposto pela parte autora\" (ou pelo INSS ...).Não diga \"Trata-se de recurso interposto contra sentença\", diga \"Trata-se de recurso interposto de sentença ...\" Não esqueça de relatar qual é o pedido final formulado no recurso ao final do texto que você escreverá. Segue o texto do recurso para sua análise:"""
        full_prompt = f"{prompt}\n\n{text_content}"

        generation_config = genai.GenerationConfig(
            temperature=1.0,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
        )

        print(f"\n{'='*80}\nStage 1: Generating initial response with Gemini\n{'='*80}\n")

        full_response = ""
        response = model.generate_content(
            full_prompt,
            generation_config=generation_config,
            stream=True
        )

        for chunk in response:
            #  Handle the chunk.text more robustly.  It *could* be None.
            if hasattr(chunk, 'text') and chunk.text:
                print(chunk.text, end="")
                full_response += chunk.text
            #  No need to catch an exception *here* specifically. Let the outer
            #  try/except handle it.  The key is that full_response is ""
            #  if there was *any* problem.

        print(f"\n{'='*80}\n")

        timestamp = generate_timestamp()
        base_name = Path(pdf_name).stem  # Use pathlib for consistent filename handling
        filename = f"{process_number or base_name}_{timestamp}.txt" # Much cleaner filename construction
        filepath = output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(full_response)

        print(f"Initial response saved to: {filepath}")
        return full_response

    except Exception as e:
        print(f"Error processing with Gemini API: {e}") # Log the error.
        return ""  # Consistent error handling:  Always return "" on error.


def review_with_gemini_pro(initial_response: str, output_dir: Path,
                          process_number: Optional[str], pdf_name: str,
                          api_key: str) -> None:
    """
    Review and improves the initial response using the Gemini Pro model.

    Args:
        initial_response: The response from the first API call.
        output_dir: Directory to save the output.
        process_number: The process number for the filename.
        pdf_name: Name of the original PDF file (for fallback filename).
        api_key: The API key to use for Gemini.

    Returns:
        None. Prints and saves the improved response.
    """
    #  Very similar structure to process_with_gemini.  Consider refactoring
    #  to avoid code duplication (see DRY principle below).
    try:
        print(f"\n{'='*80}\nStage 2: Reviewing and improving the response with Gemini Pro\n{'='*80}\n")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")  # Consider model as parameter

        review_prompt = """Atue como um excelente assistente jurídico de um juiz federal. Sua função é apenas aprimorar o texto a seguir. Não é preciso expandi-lo ou transforma-lo em uma petição. O texto deve iniciar com Trata-se de recurso inominado interposto por ... de sentença ... Você deve apenas aprimorar a redação, principalmente evitando repetições. O texto a seguir constitui um resumo, uma listagem dos principais argumentos de um recurso. Elimine repetições que prejudiquem a boa leitura do texto. Não utilize itens, tópicos ou markdown na resposta. Não utilize \"juiz de piso\" ou \"sentença de piso\". Se encontrar essas expressões, substitua-as por Juízo de origem ou sentença ou sentença recorrida. """
        full_prompt = f"{review_prompt}\n\n{initial_response}"

        generation_config = genai.GenerationConfig(
            temperature=1.0,
            top_p=0.95,
            top_k=64,  # Different top_k, consider making this a parameter
            max_output_tokens=8192,
        )

        improved_response = ""
        response = model.generate_content(
            full_prompt,
            generation_config=generation_config,
            stream=True
        )

        for chunk in response:
              if hasattr(chunk, 'text') and chunk.text:
                print(chunk.text, end="")
                improved_response += chunk.text

        print(f"\n{'='*80}\n")

        timestamp = generate_timestamp()
        base_name = Path(pdf_name).stem
        filename = f"{process_number or base_name}_improved_{timestamp}.txt"
        filepath = output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(improved_response)

        print(f"Improved response saved to: {filepath}")

    except Exception as e:
        print(f"Error in second-stage processing: {e}") # Log the error.
        #  No return value needed, as the function is void.



def main():
    """
    Main function to process all PDF files in the 'docs' folder.
    """
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        print("Please add it to your .env file as: GEMINI_API_KEY=your-api-key")
        return

    current_dir = Path.cwd()
    docs_dir = current_dir / "docs"
    output_dir = current_dir / "responses"

    if not docs_dir.exists():
        print(f"Error: Directory '{docs_dir}' does not exist.")
        print(f"Creating the directory '{docs_dir}'.")
        docs_dir.mkdir(parents=True, exist_ok=True)  # Create parent dirs if needed
        print(f"Please place your PDF files in the '{docs_dir}' directory and run the script again.")
        return

    output_dir.mkdir(exist_ok=True)
    print(f"Output will be saved to '{output_dir}'.")

    pdf_files = list(docs_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in '{docs_dir}'.")
        return

    print(f"Found {len(pdf_files)} PDF file(s) in '{docs_dir}'.")

    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")
        text_content = extract_text_from_pdf(pdf_path)

        if not text_content:
            print(f"Skipping {pdf_path.name}: No text content extracted.")
            continue

        print(f"Successfully extracted {len(text_content)} characters from {pdf_path.name}.")

        process_number = extract_process_number(text_content)
        if process_number:
            print(f"Process number extracted from PDF: {process_number}")
        else:
            print("No process number found in the PDF content.")

        initial_response = process_with_gemini(text_content, output_dir,
                                              pdf_path.name, process_number,
                                              api_key)

        if initial_response:
            review_with_gemini_pro(initial_response, output_dir,
                                  process_number, pdf_path.name, api_key)

    print("\nAll PDF files processed.")


if __name__ == "__main__":
    main()