## Importing libraries and files
import os
import re
from dotenv import load_dotenv
load_dotenv()

from crewai_tools import tool
from langchain_community.document_loaders import PyPDFLoader

## Creating custom pdf reader tool
class FinancialDocumentTool:
    @staticmethod
    @tool("Read Financial Document")
    def read_data_tool(path: str = 'data/sample.pdf') -> str:
        """Tool to read and extract text data from a PDF financial document.
        
        This tool loads a PDF file, extracts all text content, and formats it
        for analysis by removing excessive whitespace while preserving structure.

        Args:
            path (str, optional): Path to the PDF file. Defaults to 'data/sample.pdf'.

        Returns:
            str: Formatted text content of the entire financial document
        """
        try:
            # Load PDF using PyPDFLoader
            loader = PyPDFLoader(path)
            docs = loader.load()

            full_report = ""
            for page in docs:
                # Extract and clean page content
                content = page.page_content
                
                # Remove excessive newlines while preserving paragraph structure
                content = re.sub(r'\n\s*\n+', '\n\n', content)
                
                # Remove excessive spaces
                content = re.sub(r' {2,}', ' ', content)
                
                full_report += content + "\n\n"
            
            return full_report.strip()
        except FileNotFoundError:
            return f"Error: File not found at path: {path}"
        except Exception as e:
            return f"Error reading PDF: {str(e)}"