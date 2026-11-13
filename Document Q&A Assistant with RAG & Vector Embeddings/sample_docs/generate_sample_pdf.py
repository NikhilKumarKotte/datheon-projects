"""
Helper script to generate a sample multi-page PDF document for testing the RAG pipeline.
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_sample_pdf(filepath: str):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=14
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#2563EB'),
        spaceBefore=12,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        spaceAfter=8
    )

    story = []

    # PAGE 1: Overview & Remote Work Policy
    story.append(Paragraph("Acme Tech Innovations - Employee Policy Handbook", title_style))
    story.append(Paragraph("<b>Document Version:</b> 3.2 | <b>Effective Date:</b> January 15, 2026", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("1. Company Mission & Core Values", heading_style))
    story.append(Paragraph(
        "Acme Tech Innovations empowers organizations worldwide through human-centric artificial intelligence and dependable cloud architecture. "
        "Our core values are Curiosity, Integrity, Rigorous Engineering, and User Empathy. All team members are expected to uphold these standards in every client interaction and product deliverable.",
        body_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. Flexible Remote Work Policy", heading_style))
    story.append(Paragraph(
        "Acme operates under a hybrid-first model. Full-time team members are permitted to work remotely up to 3 days per week. "
        "Core collaboration hours across all teams are set between 10:00 AM and 3:00 PM Eastern Time (ET). "
        "Employees requesting international remote work must notify People Operations at least 30 business days in advance to comply with local tax and data governance regulations.",
        body_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("3. Home Office Equipment Stipend", heading_style))
    story.append(Paragraph(
        "Upon joining Acme, each full-time employee receives a one-time home office equipment stipend of $1,200 USD. "
        "This allowance may be used for ergonomic chairs, monitors, noise-canceling headphones, and standing desks. "
        "Additionally, a monthly recurring internet reimbursement of $75 USD is disbursed automatically with payroll.",
        body_style
    ))

    story.append(PageBreak())

    # PAGE 2: Leaves, Vacation & Health Benefits
    story.append(Paragraph("Acme Tech Innovations - Employee Policy Handbook", title_style))
    story.append(Paragraph("4. Paid Time Off (PTO) & Leave Accrual", heading_style))
    story.append(Paragraph(
        "Full-time employees receive 24 days of paid vacation per calendar year, accruing at a rate of 2 days per completed month of service. "
        "A maximum of 5 unused vacation days may be rolled over into the subsequent calendar year, expiring on March 31. "
        "In addition to standard vacation days, Acme offers 10 dedicated company holidays, 8 sick days, and 3 personal wellness days.",
        body_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("5. Parental & Family Care Leave", heading_style))
    story.append(Paragraph(
        "Acme provides up to 16 weeks of fully paid parental leave to all new parents (including birthing, non-birthing, and adoptive parents) "
        "who have completed at least 6 months of continuous employment. Parental leave may be taken continuously or in two separate blocks within the child's first 12 months.",
        body_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("6. Healthcare and Wellness Benefits", heading_style))
    story.append(Paragraph(
        "Acme covers 100% of employee premium contributions for comprehensive medical, dental, and vision health insurance plans under the Platinum Shield tier. "
        "Dependents are covered at an 80% subsidy level. All staff also receive free access to the Calm and Headspace mental health platforms, plus an annual fitness reimbursement of $600 USD.",
        body_style
    ))

    story.append(PageBreak())

    # PAGE 3: Data Security, AI Usage & Whistleblower Policy
    story.append(Paragraph("Acme Tech Innovations - Employee Policy Handbook", title_style))
    story.append(Paragraph("7. Responsible Artificial Intelligence Usage", heading_style))
    story.append(Paragraph(
        "All engineers and data scientists utilizing generative AI tools must adhere to the Acme Responsible AI Charter. "
        "Client proprietary source code and protected health information (PHI) must never be pasted into public, non-enterprise LLM prompts. "
        "Any external model fine-tuning requires written approval from the Chief Information Security Officer (CISO).",
        body_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("8. Information Security & Incident Response", heading_style))
    story.append(Paragraph(
        "All company laptops must run full-disk encryption (FileVault or BitLocker) and enforce Multi-Factor Authentication (MFA) with FIDO2 hardware keys or authenticator apps. "
        "In the event of a suspected security breach, compromised credentials, or lost hardware, employees must notify security@acme-tech.example within 60 minutes of detection.",
        body_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("9. Annual Professional Development Fund", heading_style))
    story.append(Paragraph(
        "Acme allocates an annual budget of $2,500 USD per employee for professional learning, including academic conferences, technical certifications, university courses, and published textbooks. "
        "Expense reimbursements must be submitted through the Expensify portal with itemized receipts within 45 days of expenditure.",
        body_style
    ))

    doc.build(story)
    print(f"Sample PDF successfully generated at: {filepath}")

if __name__ == "__main__":
    generate_sample_pdf("sample_docs/acme_employee_handbook.pdf")
