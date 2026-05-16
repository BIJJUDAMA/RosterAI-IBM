
import os
import sys
import logging

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorDevice, AcceleratorOptions
from rich.console import Console

console = Console()

def download_docling_models():
    console.print("[bold cyan]Starting Docling Model Pre-download to Repository...[/bold cyan]")
    
    # Target local directory in the repo
    artifacts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "docling"))
    if not os.path.exists(artifacts_path):
        os.makedirs(artifacts_path, exist_ok=True)
        
    # Configure options exactly as used in the application
    pipeline_options = PdfPipelineOptions(artifacts_path=artifacts_path)
    pipeline_options.do_ocr = False  # Matches app/processing/document_extractor.py
    pipeline_options.accelerator_options = AcceleratorOptions(
        num_threads=4, 
        device=AcceleratorDevice.CPU
    )

    console.print(f"[yellow]Initializing DocumentConverter with artifacts_path: {artifacts_path}[/yellow]")
    console.print("[dim]This will download the Layout and Table models directly into the repo's models/ directory.[/dim]")
    
    try:
        # Initializing the converter triggers the download to the specified artifacts_path
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        console.print(f"[green]✓ Initialization complete. Models are now stored in: {artifacts_path}[/green]")
        console.print("[blue]The system is now ready for offline/fast ingestion.[/blue]")
        
    except Exception as e:
        console.print(f"[bold red]Error during model download:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_docling_models()
