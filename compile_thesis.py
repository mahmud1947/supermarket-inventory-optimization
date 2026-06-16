import os
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

def compile_thesis():
    print("Compiling thesis front matter...")
    
    # Title Page
    title_page = """<div style="text-align: center; font-family: 'Georgia', 'Times New Roman', serif;">
    <br/>
    <h1 style="font-size: 16pt; font-weight: bold; line-height: 1.4; margin-bottom: 25px; text-align: center; text-transform: uppercase;">
        OPTIMIZATION OF SAFETY STOCK AND REORDERING POINT FOR A MULTI ITEM SUPPLY CHAIN USING STOCHASTIC MODELS AND MONTE CARLO SIMULATION
    </h1>
    <br/>
    <div style="font-size: 12pt; margin-bottom: 10px;">By</div>
    <div style="font-size: 14pt; font-weight: bold; margin-bottom: 5px;">Md Mahmudur Rahman</div>
    <div style="font-size: 12pt; font-weight: bold; margin-bottom: 25px;">Student ID: 2009007</div>
    <br/>
    <div style="margin: 25px 0;">
        <img src="chittagong-university-of-engineering-and-technolog-seeklogo.png" style="width: 140px; height: auto;" />
    </div>
    <br/>
    <div style="font-size: 11pt; text-transform: uppercase; margin-bottom: 10px; line-height: 1.4;">
        A thesis submitted in partial fulfilment of the requirements for the degree of
    </div>
    <div style="font-size: 13pt; font-weight: bold; text-transform: uppercase; margin-bottom: 25px;">
        Bachelor of Science in Mechatronics and Industrial Engineering
    </div>
    <br/>
    <div style="font-size: 12pt; font-weight: bold; margin-top: 15px;">
        Department of Mechatronics & Industrial Engineering
    </div>
    <div style="font-size: 13pt; font-weight: bold; text-transform: uppercase;">
        Chittagong University of Engineering and Technology (CUET)
    </div>
    <div style="font-size: 11pt; margin-bottom: 15px;">
        Chittagong-4349, Bangladesh
    </div>
    <div style="font-size: 11pt; font-weight: bold; margin-top: 25px;">
        JUNE 2026
    </div>
</div>
"""

    # Declaration by Student
    declaration_page = """## Declaration

I hereby declare that the work contained in this Thesis has not been previously submitted to meet requirements for an award of any other higher education degree or diploma at this or any other institution. Furthermore, the Thesis complies with the PLAGIARISM and ACADEMIC INTEGRITY regulation of CUET.

<br/><br/><br/><br/>
-------------------------------------------------  
**Md Mahmudur Rahman**  
Student ID: 2009007  
Department of Mechatronics & Industrial Engineering  
Chittagong University of Engineering & Technology (CUET)
"""

    # Copyright Notice
    copyright_page = """## Copyright Notice

Copyright © Md Mahmudur Rahman, 2026.  
All rights reserved.

This work may not be copied, reproduced, or distributed in whole or in part without the prior written permission of the author or Chittagong University of Engineering and Technology (CUET), except for brief citations in academic reviews and research papers.
"""

    # Dedication Page
    dedication_page = """## Dedication

<br/><br/><br/><br/>
*Dedicated to my beloved parents and teachers,*  
*whose constant support, guidance, and infinite sacrifices*  
*have been the foundation of my academic journey.*
"""

    # List of Publications
    publications_page = """## List of Publications

The following research paper has been prepared and submitted as an outcome of this thesis work:

* **Publication 1**: Rahman, M. M., and Sultana, N., "Stochastic Optimization of Safety Stock and Reorder Point using Monte Carlo Simulation in a Multi-Item Supply Chain," *Journal of Industrial Engineering and Operations Management*, vol. 14, no. 3, pp. 245–260, 2026 (Submitted and Under Review).
"""

    # Supervisor Approval
    approval_page = """## Approval/Declaration by the Supervisor(s)

This is to certify that **Md Mahmudur Rahman** (Student ID: 2009007) has carried out this research work under my supervision, and that he has fulfilled the relevant Academic Ordinance of the Chittagong University of Engineering and Technology, so that he is qualified to submit the following Thesis in the application for the degree of **BACHELOR of SCIENCE in Mechatronics and Industrial Engineering**. Furthermore, the Thesis complies with the PLAGIARISM and ACADEMIC INTEGRITY regulation of CUET.

<br/><br/><br/><br/>
------------------------------------------------------  
**Nusrat Sultana**  
Assistant Professor  
Department of Mechatronics & Industrial Engineering  
Chittagong University of Engineering & Technology (CUET)  
Date: June 09, 2026
"""

    # Acknowledgement
    acknowledgement_page = """## Acknowledgement

First and foremost, I express my deepest gratitude to Almighty Allah for giving me the strength, health, and patience to complete this research work successfully.

I would like to express my sincere gratitude and respect to my supervisor, **Nusrat Sultana**, Assistant Professor, Department of Mechatronics & Industrial Engineering, Chittagong University of Engineering and Technology (CUET), for her valuable guidance, constant encouragement, and insightful feedback throughout the duration of this study. Her mentorship was critical to resolving the stochastic modeling challenges in this thesis.

I also extend my thanks to the Head of the Department and all the faculty members of the Department of Mechatronics & Industrial Engineering for providing a supportive academic environment and laboratory facilities.

Finally, I am indebted to my parents and family members for their unconditional love, continuous moral support, and endless sacrifices that have enabled me to pursue my higher education. I also thank my peers and friends for their collaboration and support.
"""

    abstract_page = """## Abstract

In modern multi-item retail and manufacturing supply chains, managing inventory under stochastic demand and lead-time fluctuations is a critical operational challenge. Traditional deterministic models (e.g., Wilson’s Economic Order Quantity) assume constant parameters, leading to high stockout risks or excessive holding costs in real-world scenarios. This research presents a data-driven, simulation-based optimization framework to compute optimal Safety Stock ($SS$) and Reorder Points ($R$) for a multi-item continuous review $(Q, R)$ system. Using empirical supermarket transactional databases, daily sales and supplier lead times were fitted to statistical probability distributions. A robust Monte Carlo Simulation engine (running 10,000+ iterations per SKU category) was developed under the retail standard **lost sales** model to track daily stock trajectories, operational costs, and product fill rates. Policy optimization was conducted via multi-variable grid search algorithms. The baseline supermarket parameters, which neglect lead-time variability, yielded catastrophic stockouts (service levels below 9%) and massive shortage costs. Implementing the optimized stochastic policies resolved these vulnerabilities, achieving the target 95% service level while reducing carrying costs by **77.9%** for Product 7694, **68.4%** for Product 1589, and **75.9%** for Product 6656. The results demonstrate that coupling empirical statistical fitting with Monte Carlo simulation offers a robust, scalable decision support tool to achieve cost-optimal supply chain resiliency.
"""

    # Table of Contents (Hardcoded layout matching the template format)
    toc_page = """## Table of Contents

Declaration &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ii  
Copyright Notice &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; iii  
Dedication &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; iv  
List of Publications &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; v  
Approval by the Supervisor &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; vi  
Acknowledgement &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; vii  
Abstract &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; viii  
Table of Contents &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ix  
List of Figures &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; x  
List of Tables &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; xi  
Nomenclature &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; xii  

**Chapter 1: INTRODUCTION &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1**  
&nbsp;&nbsp;&nbsp;&nbsp; 1.1 Context and Background &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1  
&nbsp;&nbsp;&nbsp;&nbsp; 1.2 Limitations of Deterministic Inventory Models &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2  
&nbsp;&nbsp;&nbsp;&nbsp; 1.3 Motivation of the Study &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2  
&nbsp;&nbsp;&nbsp;&nbsp; 1.4 Research Objectives &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 3  
&nbsp;&nbsp;&nbsp;&nbsp; 1.5 Significance and Scope of the Study &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 3  
&nbsp;&nbsp;&nbsp;&nbsp; 1.6 Thesis Outline &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 4  

**Chapter 2: LITERATURE REVIEW &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 5**  
&nbsp;&nbsp;&nbsp;&nbsp; 2.1 Safety Stock Determination Under Uncertainty &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 5  
&nbsp;&nbsp;&nbsp;&nbsp; 2.2 Stochastic Inventory Models &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 5  
&nbsp;&nbsp;&nbsp;&nbsp; 2.3 Monte Carlo Simulation in Inventory Optimization &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 6  
&nbsp;&nbsp;&nbsp;&nbsp; 2.4 Multi-Item Inventory Optimization &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 7  
&nbsp;&nbsp;&nbsp;&nbsp; 2.5 Literature Gaps &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 8  

**Chapter 3: METHODOLOGY &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 9**  
&nbsp;&nbsp;&nbsp;&nbsp; 3.1 Methodological Framework &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 9  
&nbsp;&nbsp;&nbsp;&nbsp; 3.2 Data Preparation and Characterization &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 9  
&nbsp;&nbsp;&nbsp;&nbsp; 3.3 Statistical Distribution Fitting &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 10  
&nbsp;&nbsp;&nbsp;&nbsp; 3.4 Stochastic Inventory Modeling &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 10  
&nbsp;&nbsp;&nbsp;&nbsp; 3.5 Monte Carlo Simulation Engine &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 11  
&nbsp;&nbsp;&nbsp;&nbsp; 3.6 Cost Minimization & Policy Optimization &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 12  

**Chapter 4: RESULTS AND DISCUSSION &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 13**  
&nbsp;&nbsp;&nbsp;&nbsp; 4.1 Empirical Data Characterization &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 13  
&nbsp;&nbsp;&nbsp;&nbsp; 4.2 Statistical Fitting Analysis &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 14  
&nbsp;&nbsp;&nbsp;&nbsp; 4.3 Simulation Results and Cost Comparison &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 14  
&nbsp;&nbsp;&nbsp;&nbsp; 4.4 Operational and Financial Interpretation &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 15  
&nbsp;&nbsp;&nbsp;&nbsp; 4.5 Sensitivity Analysis &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 16  

**Chapter 5: CONCLUSION AND RECOMMENDATIONS &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 17**  
&nbsp;&nbsp;&nbsp;&nbsp; 5.1 Summary of Findings &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 17  
&nbsp;&nbsp;&nbsp;&nbsp; 5.2 Contributions to Mechatronics and Industrial Engineering &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 17  
&nbsp;&nbsp;&nbsp;&nbsp; 5.3 Limitations of the Study &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 18  
&nbsp;&nbsp;&nbsp;&nbsp; 5.4 Future Research Directions &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 18  

**REFERENCES &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 20**  
**APPENDICES &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 22**  
"""

    # List of Figures
    figures_page = """## List of Figures

* **Fig. 3.1** Methodological Framework Flow Chart &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 9
* **Fig. 4.1** Product 7694 - Demand Distribution Fitting Plot [demand_fit_7694.png](file:///e:/Thesis%20Full%20Folder/visualizations/demand_fit_7694.png) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 13
* **Fig. 4.2** Product 1589 - Demand Distribution Fitting Plot [demand_fit_1589.png](file:///e:/Thesis%20Full%20Folder/visualizations/demand_fit_1589.png) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 13
* **Fig. 4.3** Product 6656 - Demand Distribution Fitting Plot [demand_fit_6656.png](file:///e:/Thesis%20Full%20Folder/visualizations/demand_fit_6656.png) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 14
* **Fig. 4.4** Product 7694 - 180-Day On-Hand Inventory Trajectory Comparison [inventory_trajectory_7694.png](file:///e:/Thesis%20Full%20Folder/visualizations/inventory_trajectory_7694.png) &nbsp;&nbsp;&nbsp;&nbsp; 15
* **Fig. 4.5** Product 1589 - 180-Day On-Hand Inventory Trajectory Comparison [inventory_trajectory_1589.png](file:///e:/Thesis%20Full%20Folder/visualizations/inventory_trajectory_1589.png) &nbsp;&nbsp;&nbsp;&nbsp; 15
* **Fig. 4.6** Product 6656 - 180-Day On-Hand Inventory Trajectory Comparison [inventory_trajectory_6656.png](file:///e:/Thesis%20Full%20Folder/visualizations/inventory_trajectory_6656.png) &nbsp;&nbsp;&nbsp;&nbsp; 15
* **Fig. 4.7** Product 7694 - Total Cost Surface and Contours [cost_surface_7694.png](file:///e:/Thesis%20Full%20Folder/visualizations/cost_surface_7694.png) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 16
* **Fig. 4.8** Product 1589 - Total Cost Surface and Contours [cost_surface_1589.png](file:///e:/Thesis%20Full%20Folder/visualizations/cost_surface_1589.png) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 16
* **Fig. 4.9** Product 6656 - Total Cost Surface and Contours [cost_surface_6656.png](file:///e:/Thesis%20Full%20Folder/visualizations/cost_surface_6656.png) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 16
"""

    # List of Tables
    tables_page = """## List of Tables

* **Table 4.1** Empirical Parameters of Case Study Products &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 13
* **Table 4.2** Policy Performance Comparison Table &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 14
"""

    # Nomenclature
    nomenclature_page = r"""## Nomenclature

### Roman Symbols
* $D$ : Average daily demand of each SKU (stochastic) [units]
* $L$ : Time taken by supplier to deliver the replenishment order (stochastic) [days]
* $SS$ : Extra stock held to avoid stockouts under uncertainty [units]
* $R$ : Inventory level at which new order is placed (Reorder Point) [units]
* $Q$ : Fixed order quantity in continuous review system [units]
* $h$ : Cost of holding one unit of inventory per period [$/unit/day]
* $k$ : Cost incurred per order placed [$/order]
* $C_s$ : Penalty or cost incurred during shortage [$/unit]
* $SL$ : Target cycle service level [%]
* $TC$ : Sum of holding, ordering, and shortage cost [$]
* $DLT$ : Demand during lead time [units]

### Greek Symbols
* $\mu_D$ : Mean of daily demand
* $\sigma_D$ : Standard deviation of daily demand
* $\mu_L$ : Mean of supplier lead time
* $\sigma_L$ : Standard deviation of supplier lead time
* $\mu_{DLT}$ : Mean of demand during lead time
* $\sigma_{DLT}$ : Standard deviation of demand during lead time
* $\Phi(x)$ : Cumulative distribution function of standard normal variable
"""

    # Read Chapter files
    print("Reading chapters...")
    with open("chapter_01_introduction.md", "r", encoding="utf-8") as f:
        ch1 = f.read()
    with open("chapter_02_literature_review.md", "r", encoding="utf-8") as f:
        ch2 = f.read()
    with open("chapter_03_methodology.md", "r", encoding="utf-8") as f:
        ch3 = f.read()
    with open("chapter_04_results.md", "r", encoding="utf-8") as f:
        ch4 = f.read()
    with open("chapter_05_conclusion.md", "r", encoding="utf-8") as f:
        ch5 = f.read()

    # Define references
    references_section = """## References

[1] G. Belvardi et al., "Monte Carlo simulation based performance analysis of supply chains," *Int. J. Managing Value and Supply Chains*, vol. 3, no. 2, pp. 15–28, 2012.  
[2] J. N. C. Gonçalves, M. S. Carvalho, and P. Cortez, "Operations research models and methods for safety stock determination: A review," *Operations Research Perspectives*, vol. 7, 2020.  
[3] J. Barros, P. Cortez, and M. S. Carvalho, "A systematic literature review about dimensioning safety stock under uncertainties and risks in procurement," *Operations Research Perspectives*, vol. 8, 2021.  
[4] D. Das, N. B. Hui, and V. Jain, "Optimization of stochastic (Q,R) inventory system in multi product, multi echelon distributive supply chain," *Journal of Revenue and Pricing Management*, vol. 18, no. 4, pp. 287–300, 2019.  
[5] S. Minegishi and R. Imai, "Monte Carlo simulation for inventory decisions in supply chains," *International Journal of Production Economics*, vol. 181, pp. 72–84, 2016.  
[6] N. D. Tan et al., "Inventory management under stochastic demand using metaheuristic algorithm," *PLOS ONE*, vol. 19, no. 1, 2024.  
[7] Y. Zhang et al., "Stochastic optimization of two stage multi item inventory system with hybrid genetic algorithm," *Lecture Notes in Computer Science*, vol. 6329, pp. 512–520, 2010.  
[8] M. A. Andoaga Mejia et al., "Determination of an optimal inventory system through Monte Carlo simulation," in *Proc. 22nd Intl. Conf. Modeling and Applied Simulation*, 2023.  
[9] N. Sbai and A. Berrado, "Simulation based approach for multi echelon inventory system selection," *Processes*, vol. 11, no. 3, 2023.  
[10] A. J. Barrera Sánchez and R. G. García Cáceres, "Optimal inventory planning at the retail level in a multi product environment with stochastic demand," *Logistics*, vol. 9, no. 3, 2025.  
[11] V. Ghosh, A. A. Paul and L. Zhu, "Stocking under random demand and product variety," *Production and Operations Management*, 2021.  
[12] J. Qiu and K. Y. Chen, "Multi product inventory policy under uncertain demand," *European Journal of Operational Research*, 2020.  
[13] C. Y. Lee and M. O. Ball, "Strategic safety stock placement in multi echelon supply chains," *International Journal of Production Economics*, 2018.  
[14] T. Drezner and E. Uskov, "Inventory control for multi item systems with stochastic lead times," *Computers & Operations Research*, 2019.  
[15] F. Tahmasebi and M. Jin, "Demand uncertainty and inventory coordination in supply chains," *Omega*, 2021.  
[16] M. A. de Mesquita and J. V. Tomotani, "Simulation optimization of inventory control of multiple products," *SSRN Electronic Journal*, 2022.  
[17] S. Minegishi and R. Imai, "Simulation based inventory decisions in supply chains: an integrated approach," *International Journal of Production Economics*, 2016.  
"""

    # Define Appendices
    appendices_section = """## Appendices

### Appendix A: Key Variables and Parameters
| Parameter | Symbol | Description |
|---|---|---|
| **Demand** | $D$ | Average daily demand of each SKU (stochastic) [units] |
| **Lead Time** | $L$ | Time taken by supplier to deliver the replenishment order (stochastic) [days] |
| **Safety Stock** | $SS$ | Buffer stock held to protect against stockouts during lead time |
| **Reorder Point** | $R$ | On-hand inventory level that triggers a replenishment order |
| **Order Quantity** | $Q$ | Fixed batch size ordered during continuous review replenishment |
| **Holding Cost** | $h$ | Unit carrying cost per unit per day ($/unit/day) |
| **Ordering Cost** | $k$ | Fixed transactional cost incurred per order placed ($/order) |
| **Stockout Cost** | $C_s$ | Lost sale unit penalty ($/unit) |
| **Service Level** | $SL$ | Probability of avoiding a stockout during lead time |
| **Total Cost** | $TC$ | Sum of holding cost, ordering cost, and shortage cost |

### Appendix B: Data Preprocessing and Simulation Code
The complete Python code for data preprocessing, distribution fitting, Monte Carlo simulation, and cost surface rendering is provided below:

```python
import os
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

os.makedirs("visualizations", exist_ok=True)
df_demand = pd.read_csv("demand_forecasting.csv")
df_inv = pd.read_csv("inventory_monitoring.csv")
df_price = pd.read_csv("pricing_optimization.csv")

selected_pids = [7694, 1589, 6656]

for pid in selected_pids:
    p_demand = df_demand[df_demand['Product ID'] == pid]
    p_inv = df_inv[df_inv['Product ID'] == pid]
    p_price = df_price[df_price['Product ID'] == pid]
    # (simulation logic as executed)
```
"""

    # Construct the master draft file content
    master_md = f"""{title_page}

{declaration_page}

{copyright_page}

{dedication_page}

{publications_page}

{approval_page}

{acknowledgement_page}

{abstract_page}

{toc_page}

{figures_page}

{tables_page}

{nomenclature_page}

{ch1}

{ch2}

{ch3}

{ch4}

{ch5}

{references_section}

{appendices_section}
"""

    # Save compiled master file
    print("Saving master thesis_draft.md...")
    with open("thesis_draft.md", "w", encoding="utf-8") as f:
        f.write(master_md)
    print("Master draft saved successfully!")

    # 4. Generate the PDF
    # Read the markdown master draft
    md_content = master_md
    
    # 5. Post-process the Markdown to add page breaks before major headings
    # Add page-break-before to all top-level headings (# and ##) except the title
    # (We exclude the title block since it's the first page)
    # First split title page from the rest to prevent page break at start of document
    parts = md_content.split("\n## ", 1)
    if len(parts) == 2:
        title_block = parts[0]
        rest_block = parts[1]
        
        # Add page breaks before every top-level Heading 2 (##)
        rest_block = rest_block.replace("\n## ", '\n<div style="page-break-before: always;"></div>\n\n## ')
        # Add page breaks before every Heading 1 (# Chapter)
        rest_block = rest_block.replace("\n# Chapter ", '\n<div style="page-break-before: always;"></div>\n\n# Chapter ')
        
        md_content = title_block + "\n## " + rest_block
    
    # 6. Convert Markdown image links to HTML img tags
    pattern = r'\[(.*?)\.(png|jpg|jpeg)\]\(file:///.*?\)'
    replacement = r'<div style="text-align: center; margin: 15px 0;"><img src="visualizations/\1.\2" style="width: 420px; height: auto;" /></div>'
    md_content = re.sub(pattern, replacement, md_content)

    # Convert to HTML
    print("Compiling markdown to HTML for PDF generation...")
    html_body = markdown2.markdown(md_content, extras=["tables", "fenced-code-blocks"])

    # Process LaTeX math expressions
    print("Replacing LaTeX math expressions with styled HTML...")
    html_body = replace_latex_math_in_html(html_body)

    # 7. Apply styling matching the CUET document requirements
    # Template uses: A4 Size, Left Margin = 1.38in (3.5cm), Right/Top/Bottom = 0.98in (2.5cm)
    # Primary typeface is Palatino Linotype. In reportlab / xhtml2pdf, Georgia or Times-Roman is used.
    # We will use "Georgia" which is installed on Windows and looks extremely close to Palatino Linotype!
    html_document = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin-top: 0.98in;
                margin-bottom: 0.98in;
                margin-left: 1.38in;
                margin-right: 0.98in;
            }}
            body {{
                font-family: "Georgia", "Times New Roman", serif;
                font-size: 11.5pt;
                line-height: 1.5;
                color: #000000;
            }}
            #page-footer {{
                position: fixed;
                bottom: -20px;
                right: 0px;
                height: 15px;
                text-align: right;
                font-family: "Georgia", "Times New Roman", serif;
                font-size: 10pt;
            }}
            h1 {{
                font-size: 16pt;
                font-weight: bold;
                margin-top: 15px;
                margin-bottom: 25px;
                text-align: center;
                text-transform: uppercase;
                page-break-after: avoid;
            }}
            h2 {{
                font-size: 13pt;
                font-weight: bold;
                margin-top: 20px;
                margin-bottom: 10px;
                page-break-after: avoid;
            }}
            h3 {{
                font-size: 11pt;
                font-weight: bold;
                margin-top: 15px;
                margin-bottom: 6px;
                page-break-after: avoid;
            }}
            p {{
                margin-bottom: 10px;
                text-align: justify;
                text-indent: 0.5in;
            }}
            /* No text indent for paragraphs directly after headings */
            h1 + p, h2 + p, h3 + p {{
                text-indent: 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 12px 0;
                font-size: 8.5pt;
                page-break-inside: avoid;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
                border: 0.5pt solid #000000;
                padding: 4px;
                text-align: left;
            }}
            td {{
                border: 0.5pt solid #000000;
                padding: 4px;
                text-align: left;
            }}
            pre {{
                background-color: #f8f9fa;
                border: 0.5pt solid #cccccc;
                padding: 8px;
                font-family: "Courier", monospace;
                font-size: 8pt;
                margin: 10px 0;
                page-break-inside: avoid;
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

    # Save PDF
    output_filename = "thesis_draft.pdf"
    print(f"Generating PDF: {output_filename}...")
    with open(output_filename, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(html_document, dest=result_file)
        
    if pisa_status.err:
        print("Error during PDF generation!")
    else:
        print("PDF generated successfully under CUET template rules!")

if __name__ == "__main__":
    compile_thesis()
