import docx
from docx.shared import Inches, Pt, RGBColor

doc = docx.Document()
for s in doc.sections:
    s.top_margin = Inches(1.0)
    s.bottom_margin = Inches(1.0)
    s.left_margin = Inches(1.0)
    s.right_margin = Inches(1.0)

p1 = doc.add_paragraph()
r1 = p1.add_run('COVER LETTER FOR MANUSCRIPT SUBMISSION\n')
r1.bold = True
r1.font.size = Pt(14)
r1.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

p_meta = doc.add_paragraph()
p_meta.add_run('To: Editor-in-Chief\nEngineering Science and Technology, an International Journal (JESTECH)\nElsevier Publishing\nDate: November 20, 2026\nSubject: Submission of Original Research Article for Peer Review\n')

p_body = doc.add_paragraph()
p_body.add_run('Dear Editor-in-Chief,\n\nWe are pleased to submit our original research manuscript entitled:\n\n')
r_title = p_body.add_run('"Spatial-Diversity Memetic Genetic Algorithm Possibilistic Fuzzy C-Means (SD-MGA-PFCM): Overcoming Mathematical Vulnerabilities in Density Peak Evolutionary Clustering"\n\n')
r_title.bold = True
r_title.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0)

p_body.add_run('for consideration for publication as an Original Research Article in Engineering Science and Technology, an International Journal (JESTECH).\n\n')

p_body.add_run('Key Contributions:\n'
'1. Formal mathematical proof and exposure of Centroid Collapse in the DP-GA-PFCM framework.\n'
'2. Formulation of the SD-MGA-PFCM architecture featuring Diversity-Preserving DPC (D-DPC), Separation Regularization with infinite repulsion barrier, and Memetic Lamarckian Local Search.\n'
'3. Rigorous validation on 8 international benchmark datasets over 30 independent runs (1,200 clusterings), achieving Wilcoxon statistical significance of p < 0.001 across all benchmarks.\n\n')

p_body.add_run('Declarations:\n'
'- This manuscript is original and has not been published or submitted elsewhere.\n'
'- All authors approve the submission.\n'
'- There are no conflicts of interest.\n\n'
'Sincerely yours,\n'
'The Author(s)\nDepartment of Computer Science and Engineering\nEmail: author@institution.edu\n')

doc.save('d:/nckh_phu/4_documents/COVER_LETTER_FOR_SUBMISSION.docx')
print('Cover letter docx created successfully!')
