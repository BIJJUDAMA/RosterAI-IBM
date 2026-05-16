import os
import fitz  # PyMuPDF
from docx import Document
import logging
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorDevice, AcceleratorOptions

from ..logging_config import logger
from ..exceptions import ExtractionError


pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False  
pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=4, 
    device=AcceleratorDevice.CPU
)

if pipeline_options.accelerator_options.device != AcceleratorDevice.CPU:
    raise RuntimeError("Security/VRAM Breach: Docling must be strictly pinned to CPU.")

docling_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

def has_native_text(file_path):

    try:
        doc = fitz.open(file_path)
        for page in doc:
            if page.get_text().strip():
                doc.close()
                return True
        doc.close()
        return False
    except Exception as e:
        logger.error(f"Text Check Failed: {e}")
        return False

def pdf_to_images(file_path, output_dir="temp_processing"):

    if not os.path.exists(file_path):
        raise ExtractionError(f"File not found: {file_path}")
        
    image_paths = []
    logger.info(f"Converting PDF to images: [bold]{os.path.basename(file_path)}[/bold]")
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        doc = fitz.open(file_path)
        if len(doc) == 0:
            raise ExtractionError(f"PDF file is empty: {file_path}")
            
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        for i, page in enumerate(doc):
      
            pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8))
            
            img_path = os.path.join(output_dir, f"{base_name}_page_{i+1}.jpg")
            pix.save(img_path, "jpg") 
            
            from PIL import Image as PILImage
            with PILImage.open(img_path) as img:
                img.save(img_path, "JPEG", quality=60, optimize=True)
                
            image_paths.append(img_path)
            logger.debug(f"Saved optimized page {i+1} as image: {img_path}")
            
        doc.close()
        logger.info(f"Successfully converted {len(image_paths)} pages to images")
    except ExtractionError:
        raise
    except Exception as e:
        logger.error(f"[bold red]Extraction Error:[/bold red] {e} [dim]({file_path})[/dim]")
        raise ExtractionError(f"Failed to convert PDF to images: {str(e)}", str(e))
    return image_paths

def extract_raw_text(file_path):
    if not os.path.exists(file_path):
        raise ExtractionError(f"File not found: {file_path}")
        
    ext = os.path.splitext(file_path)[1].lower()
    logger.info(f"Extracting structured text from {ext.upper()} file: [bold]{os.path.basename(file_path)}[/bold]")
    text = ""
    try:
        if ext in [".pdf", ".png", ".jpg", ".jpeg"]:
            result = docling_converter.convert(file_path)
            text = result.document.export_to_markdown()
        elif ext == ".docx":
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            raise ExtractionError(f"Unsupported file format: {ext}")
            
        logger.info(f"Extracted [bold]{len(text)}[/bold] characters of structured text")
    except ExtractionError:
        raise
    except Exception as e:
        logger.error(f"[bold red]Structured Extraction Error:[/bold red] {e} [dim]({file_path})[/dim]")
        raise ExtractionError(f"Failed to extract structured text: {str(e)}", str(e))
    return text

