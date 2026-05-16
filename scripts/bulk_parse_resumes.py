import os
from pathlib import Path
from docling.document_converter import DocumentConverter
from rich.console import Console
from rich.progress import Progress

console = Console()

def bulk_parse():
    input_dir = Path("resumes")
    output_dir = Path("parsed_resumes")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    

    converter = DocumentConverter()
    
    files = [f for f in input_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
    
    if not files:
        console.print("[yellow]No resumes found in 'resumes/' directory.[/yellow]")
        return

    console.print(f"[bold blue]Starting bulk parse of {len(files)} documents using Docling...[/bold blue]")

    with Progress() as progress:
        task = progress.add_task("[cyan]Parsing documents...", total=len(files))
        
        for file_path in files:
            try:
                result = converter.convert(file_path)
                
                content = result.document.export_to_markdown()
                
                output_file = output_dir / f"{file_path.stem}.md"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(content)
                
                progress.update(task, advance=1, description=f"[cyan]Parsed: {file_path.name}")
            except Exception as e:
                console.print(f"[red]Failed to parse {file_path.name}: {e}[/red]")
                progress.update(task, advance=1)

    console.print(f"\n[bold green]Success![/bold green] Parsed resumes are in [underline]{output_dir.absolute()}[/underline]")

if __name__ == "__main__":
    bulk_parse()
