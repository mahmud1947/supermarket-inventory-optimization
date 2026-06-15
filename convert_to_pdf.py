import re
import markdown2
from xhtml2pdf import pisa

def translate_math_to_html(formula):
    # 1. Clean up spacing commands
    formula = re.sub(r'\\(;|quad|qquad|,|!|:)\s*', ' ', formula)
    formula = re.sub(r'\\\s+', ' ', formula)
    
    # 2. Text placeholders: \text{...} using TEXTPxx (no underscores to avoid subscript matching)
    texts = []
    def save_text(m):
        texts.append(m.group(1))
        return f"TEXTP{len(texts)-1}"
    formula = re.sub(r'\\text\{([^}]+)\}', save_text, formula)
    formula = re.sub(r'\\text\s+([a-zA-Z]+)', save_text, formula)
    
    # 3. Brackets & functions first (to avoid collision with \le etc.)
    formula = re.sub(r'\\left\(', '(', formula)
    formula = re.sub(r'\\right\)', ')', formula)
    formula = re.sub(r'\\left\[', '[', formula)
    formula = re.sub(r'\\right\]', ']', formula)
    formula = re.sub(r'\\lfloor', '&lfloor;', formula)
    formula = re.sub(r'\\rfloor', '&rfloor;', formula)
    formula = re.sub(r'\\lceil', '&lceil;', formula)
    formula = re.sub(r'\\rceil', '&rceil;', formula)
    
    formula = re.sub(r'\\(min|max|sup|exp|log|sin|cos)(?![a-zA-Z])', r'\1', formula)
    
    # 4. Greek letters & Math operators
    greek_symbols = {
        r'\\mu': '&mu;',
        r'\\sigma': '&sigma;',
        r'\\Phi': '&Phi;',
        r'\\lambda': '&lambda;',
        r'\\beta': '&beta;',
        r'\\alpha': '&alpha;',
        r'\\pi': '&pi;',
        r'\\theta': '&theta;',
        r'\\delta': '&delta;',
        r'\\Delta': '&Delta;',
    }
    for latex, html in greek_symbols.items():
        formula = re.sub(latex, html, formula)
        
    formula = re.sub(r'\\in(?![a-zA-Z])', '&isin;', formula)
    
    math_ops = {
        r'\\cdot': '&middot;',
        r'\\times': '&times;',
        r'\\le': '&le;',
        r'\\ge': '&ge;',
        r'\\notin': '&notin;',
        r'\\isin': '&isin;',
        r'\\approx': '&approx;',
        r'\\sim': '~',
        r'\\pm': '&plusmn;',
        r'\\infty': '&infin;',
        r'\\mathrel\{\+\}=': '+=',
        r'\\mathrel\{\-\}=': '-=',
    }
    for latex, html in math_ops.items():
        formula = re.sub(latex, html, formula)

    # 5. Fractions
    while r'\frac' in formula:
        new_formula = re.sub(r'\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}', r'<sup>\1</sup>&frasl;<sub>\2</sub>', formula)
        if new_formula == formula:
            break
        formula = new_formula

    # 6. Subscripts and superscripts
    formula = re.sub(r'\^\{([^{}]+)\}', r'<sup>\1</sup>', formula)
    formula = re.sub(r'\^([a-zA-Z0-9*-]+)', r'<sup>\1</sup>', formula)
    formula = re.sub(r'_\{([^{}]+)\}', r'<sub>\1</sub>', formula)
    formula = re.sub(r'_([a-zA-Z0-9,]+)', r'<sub>\1</sub>', formula)

    # 7. Square roots
    while r'\sqrt' in formula:
        new_formula = re.sub(r'\\sqrt\s*\{([^{}]+)\}', r'&radic;[ \1 ]', formula)
        if new_formula == formula:
            break
        formula = new_formula

    # 8. Sums
    formula = re.sub(r'\\sum\b', '&Sigma;', formula)

    # 9. Italicize variables
    tokens = re.split(r'(</?[a-zA-Z]+[^>]*>|&[a-zA-Z]+;)', formula)
    for idx, token in enumerate(tokens):
        if not (token.startswith('<') or token.startswith('&')):
            def repl_var(m):
                word = m.group(0)
                if word.lower() in ['min', 'max', 'sup', 'exp', 'log', 'sin', 'cos', 'where', 'and', 'or', 'for', 'of', 'in', 'transit']:
                    return word
                if word.isdigit():
                    return word
                if word.startswith('TEXTP'):
                    return word
                return f'<i>{word}</i>'
            
            token = re.sub(r'\b[a-zA-Z][a-zA-Z0-9_]*\b', repl_var, token)
            tokens[idx] = token
    formula = "".join(tokens)

    # 10. Replace text placeholders
    for idx, original_text in enumerate(texts):
        formula = formula.replace(f"TEXTP{idx}", f'<span style="font-style: normal; font-family: \'Georgia\', \'Times New Roman\', serif;">{original_text}</span>')
        
    return formula

def replace_latex_math_in_html(html_content):
    # First protect currency signs
    html_content = html_content.replace('($)', '(&#36;)')
    html_content = html_content.replace('$/', '&#36;/')
    html_content = html_content.replace('[$]', '[&#36;]')
    html_content = re.sub(r'\$(?=\d)', '&#36;', html_content)
    
    code_pattern = re.compile(r'(<pre>.*?</pre>|<code>.*?</code>)', re.DOTALL)
    parts = code_pattern.split(html_content)
    
    for i in range(0, len(parts), 2):
        content = parts[i]
        
        # 1. Block math: $$(.*?)$$
        def repl_block_math(match):
            math_content = match.group(1).strip()
            html_math = translate_math_to_html(math_content)
            return f'<div style="text-align: center; margin: 12px 0; font-size: 13pt; font-family: \'Georgia\', \'Times New Roman\', serif;">{html_math}</div>'
            
        content = re.sub(r'\$\$(.*?)\$\$', repl_block_math, content, flags=re.DOTALL)
        
        # 2. Inline math: $(.*?)$
        def repl_inline_math(match):
            math_content = match.group(1).strip()
            html_math = translate_math_to_html(math_content)
            return f'<span style="font-family: \'Georgia\', \'Times New Roman\', serif;">{html_math}</span>'
            
        content = re.sub(r'\$([^\$\n]+)\$', repl_inline_math, content)
        
        parts[i] = content
        
    return "".join(parts)

def convert_md_to_pdf():
    print("Reading thesis_draft.md...")
    with open("thesis_draft.md", "r", encoding="utf-8") as f:
        md_content = f.read()

    # 1. Post-process the Markdown to add page breaks before chapters
    md_content = re.sub(r'(# Chapter \d+)', r'<div style="page-break-before: always;"></div>\n\n\1', md_content)
    # Page breaks before other major sections
    for section in ["## DECLARATION", "## ABSTRACT", "## TABLE OF CONTENTS", "## LIST OF FIGURES", "## LIST OF TABLES", "## REFERENCES", "## APPENDICES"]:
        md_content = md_content.replace(section, f'<div style="page-break-before: always;"></div>\n\n{section}')

    # 2. Convert Markdown image links to HTML img tags
    # Example: [demand_fit_7694.png](file:///e:/Thesis%20Full%20Folder/visualizations/demand_fit_7694.png)
    # We replace it with standard HTML img tag referencing the local visualizations folder
    pattern = r'\[(.*?)\.(png|jpg|jpeg)\]\(file:///.*?\)'
    replacement = r'<div style="text-align: center; margin: 15px 0;"><img src="visualizations/\1.\2" style="width: 380px; height: auto;" /></div>'
    md_content = re.sub(pattern, replacement, md_content)

    # 3. Compile Markdown to HTML
    print("Compiling markdown to HTML...")
    html_body = markdown2.markdown(md_content, extras=["tables", "fenced-code-blocks"])

    # Process LaTeX math expressions
    print("Replacing LaTeX math expressions with styled HTML...")
    html_body = replace_latex_math_in_html(html_body)

    # 4. Wrap with academic CSS and layout
    html_document = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: letter;
                margin: 0.6in;
            }}
            body {{
                font-family: "Times-Roman", "Times New Roman", serif;
                font-size: 11pt;
                line-height: 1.4;
                color: #000000;
            }}
            #page-footer {{
                position: fixed;
                bottom: -20px;
                right: 0px;
                height: 15px;
                text-align: right;
                font-family: "Times-Roman", "Times New Roman", serif;
                font-size: 10pt;
            }}
            h1 {{
                font-size: 15pt;
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 15px;
                text-align: center;
                text-transform: uppercase;
            }}
            h2 {{
                font-size: 12pt;
                font-weight: bold;
                margin-top: 15px;
                margin-bottom: 8px;
            }}
            h3 {{
                font-size: 10.5pt;
                font-weight: bold;
                margin-top: 12px;
                margin-bottom: 6px;
            }}
            p {{
                margin-bottom: 8px;
                text-align: justify;
                text-indent: 0.5in;
            }}
            h1 + p, h2 + p, h3 + p {{
                text-indent: 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 12px 0;
                font-size: 8pt;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
                border: 0.5pt solid #000000;
                padding: 3px;
                text-align: left;
            }}
            td {{
                border: 0.5pt solid #000000;
                padding: 3px;
                text-align: left;
            }}
            pre {{
                background-color: #f8f9fa;
                border: 0.5pt solid #cccccc;
                padding: 6px;
                font-family: "Courier", monospace;
                font-size: 8pt;
                margin: 8px 0;
            }}
            code {{
                font-family: "Courier", monospace;
                font-size: 8.5pt;
                background-color: #f4f4f4;
            }}
        </style>
    </head>
    <body>
        <div id="page-footer">Page <pdf:pagenumber></div>
        {html_body}
    </body>
    </html>
    """

    # 5. Output to PDF
    output_filename = "thesis_draft.pdf"
    print(f"Generating PDF: {output_filename}...")
    with open(output_filename, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(html_document, dest=result_file)
        
    if pisa_status.err:
        print("Error during PDF generation!")
    else:
        print("PDF generated successfully!")

if __name__ == "__main__":
    convert_md_to_pdf()
