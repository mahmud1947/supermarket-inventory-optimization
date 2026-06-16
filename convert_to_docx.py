import os
import re
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner margins (padding) for a table cell in dxa (1 dxa = 1/20 pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_borders(cell, color="CCCCCC", sz="4", val="single"):
    """Set thin borders for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for border_name in ['w:top', 'w:left', 'w:bottom', 'w:right']:
        node = OxmlElement(border_name)
        node.set(qn('w:val'), val)
        node.set(qn('w:sz'), sz)
        node.set(qn('w:space'), '0')
        node.set(qn('w:color'), color)
        tcBorders.append(node)
    tcPr.append(tcBorders)

def parse_runs(paragraph, text, default_font="Georgia"):
    """
    Parses bold (**), italic (*), and inline math ($) patterns.
    Applies appropriate run properties (bold, italic, sub/sup) in Word.
    """
    # Pattern to tokenize: Math ($...$), Bold (**...**), Italic (*...*)
    tokens = re.split(r'(\$\$[^\$]+\$\$|\$[^\$]+\$|\*\*[^*]+\*\*|\*[^*]+\*)', text)
    
    for token in tokens:
        if not token:
            continue
            
        # Math Block ($$ ... $$) or Inline Math ($ ... $)
        if token.startswith('$'):
            is_block = token.startswith('$$')
            math_content = token.strip('$ ')
            
            # Clean up latex keywords
            math_content = re.sub(r'\\(mu|sigma|lambda|beta|alpha|pi|theta|delta|Phi|Delta)', lambda m: {
                'mu': 'μ', 'sigma': 'σ', 'lambda': 'λ', 'beta': 'β', 'alpha': 'α',
                'pi': 'π', 'theta': 'θ', 'delta': 'δ', 'Phi': 'Φ', 'Delta': 'Δ'
            }[m.group(1)], math_content)
            
            # Common symbols
            math_content = math_content.replace(r'\cdot', '·')
            math_content = math_content.replace(r'\times', '×')
            math_content = math_content.replace(r'\le', '≤')
            math_content = math_content.replace(r'\ge', '≥')
            math_content = math_content.replace(r'\approx', '≈')
            math_content = math_content.replace(r'\infty', '∞')
            math_content = math_content.replace(r'\sum', 'Σ')
            math_content = math_content.replace(r'\text', '')
            math_content = math_content.replace(r'\left(', '(').replace(r'\right)', ')')
            math_content = math_content.replace(r'\left[', '[').replace(r'\right]', ']')
            math_content = re.sub(r'\\(quad|qquad|;|!|,)', ' ', math_content)
            math_content = math_content.replace('\\', '')
            
            # Parse subscripts (_) and superscripts (^)
            # We break the math token down into base, subscripts, and superscripts
            sub_sup_tokens = re.split(r'(_\{[^}]+\}|_[a-zA-Z0-9*+-]+|\^\{[^}]+\}|\^[a-zA-Z0-9*+-]+)', math_content)
            
            for s_token in sub_sup_tokens:
                if not s_token:
                    continue
                run = paragraph.add_run()
                run.font.name = default_font
                run.font.size = Pt(11.5)
                
                if s_token.startswith('_'):
                    clean_val = s_token[1:].strip('{}')
                    run.text = clean_val
                    run.font.subscript = True
                    run.font.italic = True
                elif s_token.startswith('^'):
                    clean_val = s_token[1:].strip('{}')
                    run.text = clean_val
                    run.font.superscript = True
                    run.font.italic = True
                else:
                    run.text = s_token
                    # Italicize math variables, but keep numbers and brackets normal
                    if re.match(r'^[a-zA-Z0-9*+-]+$', s_token) and not s_token.isdigit():
                        run.font.italic = True
                    
        # Bold (** ... **)
        elif token.startswith('**') and token.endswith('**'):
            run = paragraph.add_run(token[2:-2])
            run.font.name = default_font
            run.font.size = Pt(11.5)
            run.font.bold = True
            
        # Italic (* ... *)
        elif token.startswith('*') and token.endswith('*'):
            run = paragraph.add_run(token[1:-1])
            run.font.name = default_font
            run.font.size = Pt(11.5)
            run.font.italic = True
            
        # Normal Text
        else:
            run = paragraph.add_run(token)
            run.font.name = default_font
            run.font.size = Pt(11.5)

def build_docx():
    print("Reading thesis_draft.md to compile into Microsoft Word format...")
    if not os.path.exists("thesis_draft.md"):
        print("Error: thesis_draft.md not found. Please compile it first.")
        return

    with open("thesis_draft.md", "r", encoding="utf-8") as f:
        content = f.read()

    doc = Document()
    
    # 1. Page Setup (CUET Academic Rules: A4, Left=1.38", Right=0.98", Top/Bottom=0.98")
    for section in doc.sections:
        section.page_width = Inches(8.27)  # A4 width
        section.page_height = Inches(11.69) # A4 height
        section.top_margin = Inches(0.98)
        section.bottom_margin = Inches(0.98)
        section.left_margin = Inches(1.38)
        section.right_margin = Inches(0.98)

    # Split document by page breaks
    pages = content.split('<div style="page-break-before: always;"></div>')

    for p_idx, page_content in enumerate(pages):
        page_content = page_content.strip()
        if not page_content:
            continue
            
        # If it's not the first page, add a page break
        if p_idx > 0:
            doc.add_page_break()

        # Check if the page is the HTML Cover Page
        if "chittagong-university-of-engineering-and-technolog-seeklogo.png" in page_content:
            # We hardcode the title page rendering for exact formatting
            print("Rendering Title Page...")
            # Title
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', page_content, re.DOTALL)
            title_text = title_match.group(1).strip() if title_match else "THESIS TITLE PLACEHOLDER"
            title_p = doc.add_paragraph()
            title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = title_p.add_run(title_text)
            run.font.name = "Georgia"
            run.font.size = Pt(16)
            run.font.bold = True
            
            # Spaces
            for _ in range(2):
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(12)

            # "By"
            by_p = doc.add_paragraph()
            by_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = by_p.add_run("By\n\n")
            run.font.name = "Georgia"
            run.font.size = Pt(12)
            
            # Author Details
            author_p = doc.add_paragraph()
            author_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run1 = author_p.add_run("Md Mahmudur Rahman\n")
            run1.font.bold = True
            run1.font.size = Pt(13)
            run2 = author_p.add_run("Student ID: 2009007")
            run2.font.bold = True
            run2.font.size = Pt(12)
            for r in [run1, run2]:
                r.font.name = "Georgia"
                
            # Logo spacing
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(18)

            # Add CUET Logo Image
            logo_path = "chittagong-university-of-engineering-and-technolog-seeklogo.png"
            if os.path.exists(logo_path):
                logo_p = doc.add_paragraph()
                logo_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                logo_p.add_run().add_picture(logo_path, width=Inches(1.5))
            
            # Spacing
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(18)

            # Degree Text
            degree_p = doc.add_paragraph()
            degree_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run1 = degree_p.add_run("A thesis submitted in partial fulfilment of the requirements for the degree of\n")
            run1.font.size = Pt(11)
            run2 = degree_p.add_run("Bachelor of Science in Mechatronics and Industrial Engineering\n")
            run2.font.bold = True
            run2.font.size = Pt(12)
            for r in [run1, run2]:
                r.font.name = "Georgia"

            # Spacing
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(24)

            # Department & University
            univ_p = doc.add_paragraph()
            univ_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run1 = univ_p.add_run("Department of Mechatronics & Industrial Engineering\n")
            run1.font.bold = True
            run1.font.size = Pt(12)
            run2 = univ_p.add_run("Chittagong University of Engineering and Technology (CUET)\n")
            run2.font.bold = True
            run2.font.size = Pt(13)
            run3 = univ_p.add_run("Chittagong-4349, Bangladesh\n\n")
            run3.font.size = Pt(11)
            run4 = univ_p.add_run("JUNE 2026")
            run4.font.bold = True
            run4.font.size = Pt(11)
            for r in [run1, run2, run3, run4]:
                r.font.name = "Georgia"
            continue

        # If the page is another HTML-heavy page (e.g. Student Declaration, Supervisor Approval, Credits)
        # We clean the HTML tags out or parse them
        if page_content.startswith("<div") or page_content.startswith("<p"):
            # Strip tags and keep structural lines
            lines = []
            for line in page_content.split("\n"):
                clean_line = re.sub(r'<[^>]+>', '', line).strip()
                if clean_line:
                    lines.append(clean_line)
            # Reconstruct content
            page_content = "\n\n".join(lines)

        # Parse standard Markdown blocks on the page
        blocks = page_content.split("\n\n")
        in_table = False
        table_rows = []
        in_code = False
        code_lines = []
        
        is_first_para = True

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # -------------------------------------------------------------
            # Code Block Start/End
            # -------------------------------------------------------------
            if block.startswith("```"):
                if not in_code:
                    in_code = True
                    code_lines.append(block.replace("```python", "").replace("```", ""))
                else:
                    in_code = False
                    # Write code block to Word
                    p = doc.add_paragraph()
                    p.paragraph_format.space_before = Pt(6)
                    p.paragraph_format.space_after = Pt(6)
                    p.paragraph_format.left_indent = Inches(0.4)
                    run = p.add_run("\n".join(code_lines))
                    run.font.name = "Courier New"
                    run.font.size = Pt(8.5)
                    code_lines = []
                continue
            
            if in_code:
                code_lines.append(block)
                continue

            # -------------------------------------------------------------
            # Table Start/Row Collection/Table End
            # -------------------------------------------------------------
            if block.startswith("|"):
                in_table = True
                table_rows.append(block)
                continue
            else:
                if in_table:
                    # Write table to Word
                    write_table_to_docx(doc, table_rows)
                    table_rows = []
                    in_table = False

            # -------------------------------------------------------------
            # Headings
            # -------------------------------------------------------------
            if block.startswith("# "):
                # Heading 1
                heading_text = block[2:].strip().upper()
                h = doc.add_heading(level=1)
                h.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = h.add_run(heading_text)
                run.font.name = "Georgia"
                run.font.size = Pt(15)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0, 0, 0)
                h.paragraph_format.space_before = Pt(18)
                h.paragraph_format.space_after = Pt(12)
                h.paragraph_format.keep_with_next = True
                is_first_para = True
                continue
                
            elif block.startswith("## "):
                # Heading 2
                heading_text = block[3:].strip()
                h = doc.add_heading(level=2)
                h.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = h.add_run(heading_text)
                run.font.name = "Georgia"
                run.font.size = Pt(12.5)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0, 0, 0)
                h.paragraph_format.space_before = Pt(14)
                h.paragraph_format.space_after = Pt(8)
                h.paragraph_format.keep_with_next = True
                is_first_para = True
                continue
                
            elif block.startswith("### "):
                # Heading 3
                heading_text = block[4:].strip()
                h = doc.add_heading(level=3)
                h.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = h.add_run(heading_text)
                run.font.name = "Georgia"
                run.font.size = Pt(11)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0, 0, 0)
                h.paragraph_format.space_before = Pt(12)
                h.paragraph_format.space_after = Pt(6)
                h.paragraph_format.keep_with_next = True
                is_first_para = True
                continue

            # -------------------------------------------------------------
            # Images (Fitted plots or flowcharts)
            # -------------------------------------------------------------
            # Example: [demand_fit_7694.png](file:///...)
            image_match = re.search(r'\[(.*?)\.(png|jpg|jpeg)\]\(file:///.*?\)', block)
            if image_match:
                img_name = f"{image_match.group(1)}.{image_match.group(2)}"
                img_path = f"visualizations/{img_name}"
                if os.path.exists(img_path):
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run().add_picture(img_path, width=Inches(4.5))
                    # Check for caption below it
                    caption_block = block.replace(image_match.group(0), "").strip()
                    if caption_block:
                        cp = doc.add_paragraph()
                        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        c_run = cp.add_run(caption_block)
                        c_run.font.name = "Georgia"
                        c_run.font.size = Pt(9.5)
                        c_run.font.italic = True
                continue

            # -------------------------------------------------------------
            # Bullet/List Items
            # -------------------------------------------------------------
            if block.startswith("* ") or block.startswith("- "):
                # Simple list item
                p = doc.add_paragraph(style='List Bullet')
                p.paragraph_format.space_after = Pt(4)
                # Remove markdown character and parse runs
                clean_text = block[2:].strip()
                parse_runs(p, clean_text)
                continue
            
            # Numbered Lists (like 1. 2. 3.)
            num_match = re.match(r'^(\d+)\.\s+(.*)', block, re.DOTALL)
            if num_match:
                p = doc.add_paragraph(style='List Number')
                p.paragraph_format.space_after = Pt(4)
                clean_text = num_match.group(2).strip()
                parse_runs(p, clean_text)
                continue

            # -------------------------------------------------------------
            # Normal Paragraph
            # -------------------------------------------------------------
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.3
            p.paragraph_format.space_after = Pt(8)
            
            # First paragraph after heading has NO indentation, subsequent paragraphs have 0.5" indent
            if not is_first_para:
                p.paragraph_format.first_line_indent = Inches(0.5)
            
            is_first_para = False
            parse_runs(p, block)
            
        # If the page ended with a table, write it out
        if in_table:
            write_table_to_docx(doc, table_rows)
            table_rows = []
            in_table = False

    # Save the output file
    output_filename = "thesis_draft.docx"
    doc.save(output_filename)
    print(f"Microsoft Word document successfully created: {output_filename}")


def write_table_to_docx(doc, table_rows):
    """Parses markdown table text and adds a styled table to docx."""
    # Separate rows into cells
    parsed_grid = []
    for r in table_rows:
        cells = [c.strip() for c in r.split("|")[1:-1]]
        # Skip separator rows like |---|---|
        if cells and all(c == "" or re.match(r'^[-:]+$', c) for c in cells):
            continue
        if cells:
            parsed_grid.append(cells)
            
    if not parsed_grid:
        return
        
    num_rows = len(parsed_grid)
    num_cols = len(parsed_grid[0])
    
    table = doc.add_table(rows=num_rows, cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    for row_idx, row_cells in enumerate(parsed_grid):
        row = table.rows[row_idx]
        for col_idx, cell_value in enumerate(row_cells):
            cell = row.cells[col_idx]
            cell.text = "" # Clear default
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            
            # Format text
            # Headers have bold text
            if row_idx == 0:
                parse_runs(p, f"**{cell_value}**")
            else:
                parse_runs(p, cell_value)
                
            # Formatting
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            set_cell_borders(cell, color="444444" if row_idx == 0 else "CCCCCC", sz="4")
            
            # Font size inside table
            for run in p.runs:
                run.font.size = Pt(8.5)


if __name__ == "__main__":
    build_docx()
