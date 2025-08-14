import subprocess
import sys
import os

def generate_pdf():
    """Generate PDF documentation from markdown file"""
    
    input_file = "OHNE_DOCUMENTATION.md"
    output_file = "Ohne_Documentation.pdf"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found!")
        return False
    
    print("📄 Generating PDF documentation...")
    
    # Simplified pandoc command without problematic parameters
    pandoc_cmd = [
        'pandoc',
        input_file,
        '-o', output_file,
        '--pdf-engine=xelatex',
        '--variable', 'geometry:margin=1in',
        '--variable', 'fontsize=11pt',
        '--variable', 'documentclass=article',
        '--variable', 'colorlinks=true',
        '--variable', 'linkcolor=blue',
        '--variable', 'urlcolor=blue',
        '--toc',
        '--toc-depth=3',
        '--number-sections'
    ]
    
    try:
        # Run pandoc command
        result = subprocess.run(pandoc_cmd, capture_output=True, text=True, check=True)
        print(f"✅ PDF generated successfully: {output_file}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating PDF: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        
        # Try alternative approach with basic pandoc
        print("\n🔄 Trying simplified approach...")
        simple_cmd = [
            'pandoc',
            input_file,
            '-o', output_file,
            '--toc'
        ]
        
        try:
            subprocess.run(simple_cmd, check=True)
            print(f"✅ PDF generated with basic formatting: {output_file}")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"❌ Basic approach also failed: {e2}")
            return False
            
    except FileNotFoundError:
        print("❌ Error: pandoc not found!")
        print("Please install pandoc:")
        print("- Windows: Download from https://pandoc.org/installing.html")
        print("- macOS: brew install pandoc")
        print("- Linux: sudo apt-get install pandoc")
        return False

def generate_html_alternative():
    """Generate HTML version as alternative to PDF"""
    
    input_file = "OHNE_DOCUMENTATION.md"
    output_file = "Ohne_Documentation.html"
    
    print("🌐 Generating HTML documentation as alternative...")
    
    html_cmd = [
        'pandoc',
        input_file,
        '-o', output_file,
        '--standalone',
        '--toc',
        '--toc-depth=3',
        '--css=style.css'
    ]
    
    try:
        subprocess.run(html_cmd, check=True)
        print(f"✅ HTML generated successfully: {output_file}")
        print("💡 You can convert HTML to PDF using your browser's 'Print to PDF' feature")
        return True
    except Exception as e:
        print(f"❌ HTML generation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Ohne - Only Vocals Documentation Generator")
    print("=" * 50)
    
    # Try PDF generation first
    if not generate_pdf():
        print("\n" + "=" * 50)
        print("📋 PDF generation failed. Trying HTML alternative...")
        generate_html_alternative()
    
    print("\n✨ Documentation generation complete!")
